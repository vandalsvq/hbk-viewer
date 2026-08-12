# -*- coding: utf-8 -*-
"""Headless-проверка формы просмотрщика справки.

    python tools/build_check.py

Та же форма, что уходит во внешнюю обработку, кладётся общей формой в одноразовую
тестовую конфигурацию. Конфигуратор проверяет синтаксис модуля и привязку элементов
(/CheckModules), затем предприятие открывает форму, гоняет её самопроверку
(form_check.bsl) и завершает работу. Кликов не требуется.

Каталог стенда - тот же, что у run.py: переменная окружения HBK_WORK, иначе временный
каталог системы. Платформа ищется сама, переопределяется переменной HBK_1C.
"""
import os, re, shutil, subprocess, sys, time, uuid

from formsrc import NS, записать, логформа, модуль_формы, читать
from стенд import РАБОЧИЙ, конфигуратор as запустить_конфигуратор, платформа, создать_иб

WORK = РАБОЧИЙ
IB = os.path.join(WORK, "ib")
CF = os.path.join(WORK, "cf")
ЛОГ = os.path.join(os.environ["TEMP"], "hbk_check.log")
ТРАССА = os.path.join(os.environ["TEMP"], "hbk_check_trace.log")
ФЛАГ = os.path.join(os.environ["TEMP"], "hbk_check_keep.flag")
ФОРМА = "ПроверкаФормы"

МОДУЛЬ = "Стенд"

ОБЩИЙ_МОДУЛЬ_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<MetaDataObject xmlns="http://v8.1c.ru/8.3/MDClasses" %(ns)s version="2.20">
\t<CommonModule uuid="%(uuid)s">
\t\t<Properties>
\t\t\t<Name>%(имя)s</Name>
\t\t\t<Synonym/>
\t\t\t<Comment/>
\t\t\t<Global>false</Global>
\t\t\t<ClientManagedApplication>false</ClientManagedApplication>
\t\t\t<Server>true</Server>
\t\t\t<ExternalConnection>false</ExternalConnection>
\t\t\t<ClientOrdinaryApplication>false</ClientOrdinaryApplication>
\t\t\t<ServerCall>true</ServerCall>
\t\t\t<Privileged>false</Privileged>
\t\t\t<ReturnValuesReuse>DontUse</ReturnValuesReuse>
\t\t</Properties>
\t</CommonModule>
</MetaDataObject>
'''

ОБЩАЯ_ФОРМА_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<MetaDataObject xmlns="http://v8.1c.ru/8.3/MDClasses" %(ns)s version="2.20">
\t<CommonForm uuid="%(uuid)s">
\t\t<Properties>
\t\t\t<Name>%(имя)s</Name>
\t\t\t<Synonym>
\t\t\t\t<v8:item>
\t\t\t\t\t<v8:lang>ru</v8:lang>
\t\t\t\t\t<v8:content>Проверка формы</v8:content>
\t\t\t\t</v8:item>
\t\t\t</Synonym>
\t\t\t<Comment/>
\t\t\t<FormType>Managed</FormType>
\t\t\t<IncludeHelpInContents>false</IncludeHelpInContents>
\t\t\t<UsePurposes>
\t\t\t\t<v8:Value xsi:type="app:ApplicationUsePurpose">PlatformApplication</v8:Value>
\t\t\t</UsePurposes>
\t\t\t<ExtendedPresentation/>
\t\t</Properties>
</CommonForm>
</MetaDataObject>
'''


def конфигуратор(*аргументы):
    return запустить_конфигуратор(IB, *аргументы)


def снять_прошлые_сеансы():
    """Снимает предприятие, оставшееся от прошлого прогона: оно держит лицензию и ИБ.

    Отбор строго по пути нашей тестовой ИБ - чужие сеансы 1С не трогаем.
    """
    команда = ("Get-CimInstance Win32_Process -Filter \"Name='1cv8.exe' or Name='1cv8c.exe'\" | "
               "Where-Object { $_.CommandLine -notlike '*DESIGNER*' -and "
               "$_.CommandLine -like '*%s*' } | ForEach-Object { $_.ProcessId }" % IB)
    вывод = subprocess.run(["powershell", "-NoProfile", "-Command", команда],
                           capture_output=True, text=True).stdout
    for строка in вывод.split():
        if строка.strip().isdigit():
            print("снимаю оставшийся сеанс предприятия:", строка.strip())
            subprocess.call(["taskkill", "/F", "/PID", строка.strip()],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def подготовить_стенд():
    os.makedirs(WORK, exist_ok=True)
    if not os.path.exists(os.path.join(IB, "1Cv8.1CD")):
        print("создаю тестовую ИБ...")
        создать_иб(IB)
    if not os.path.exists(os.path.join(CF, "Configuration.xml")):
        print("выгружаю конфигурацию в файлы...")
        конфигуратор("/DumpConfigToFiles", CF)


def добавить_общую_форму():
    """Кладёт форму и служебный модуль в выгрузку конфигурации и прописывает их в состав."""
    for каталог in ("CommonForms", "CommonModules"):
        путь = os.path.join(CF, каталог)
        if os.path.isdir(путь):
            shutil.rmtree(путь)

    записать(os.path.join(CF, "CommonForms", ФОРМА + ".xml"),
             ОБЩАЯ_ФОРМА_XML % {"ns": NS, "uuid": str(uuid.uuid4()), "имя": ФОРМА})
    записать(os.path.join(CF, "CommonForms", ФОРМА, "Ext", "Form.xml"), логформа())
    записать(os.path.join(CF, "CommonForms", ФОРМА, "Ext", "Form", "Module.bsl"),
             модуль_формы((("form_check.bsl", "Самопроверка"),)))

    записать(os.path.join(CF, "CommonModules", МОДУЛЬ + ".xml"),
             ОБЩИЙ_МОДУЛЬ_XML % {"ns": NS, "uuid": str(uuid.uuid4()), "имя": МОДУЛЬ})
    записать(os.path.join(CF, "CommonModules", МОДУЛЬ, "Ext", "Module.bsl"), читать("check_server.bsl"))

    # Состав переписываем начисто: выгрузка живёт между прогонами, и строки бы копились.
    путь = os.path.join(CF, "Configuration.xml")
    строки = [с for с in open(путь, encoding="utf-8-sig").read().split("\n")
              if "<CommonForm>" not in с and "<CommonModule>" not in с]
    метка = "\t\t<ChildObjects>"
    состав = ["\t\t\t<CommonModule>%s</CommonModule>" % МОДУЛЬ,
              "\t\t\t<CommonForm>%s</CommonForm>" % ФОРМА]
    место = строки.index(метка) + 1
    строки[место:место] = состав
    записать(путь, "\n".join(строки))

    # Конфигуратор сверяется со слепком выгрузки и может не заметить новый объект.
    слепок = os.path.join(CF, "ConfigDumpInfo.xml")
    if os.path.exists(слепок):
        os.remove(слепок)

    записать(os.path.join(CF, "Ext", "ManagedApplicationModule.bsl"), читать("check_app.bsl"))


def main():
    оставить_окно = "--окно" in sys.argv

    снять_прошлые_сеансы()
    подготовить_стенд()
    добавить_общую_форму()

    часы = time.time()
    код, текст = конфигуратор("/LoadConfigFromFiles", CF)
    print("загрузка конфигурации: код=%s (%.1f c)" % (код, time.time() - часы))
    if код != 0:
        print(текст[:4000])
        return 1

    часы = time.time()
    код, текст = конфигуратор("/UpdateDBCfg")
    print("обновление базы: код=%s (%.1f c)" % (код, time.time() - часы))
    if код != 0:
        print(текст[:4000])
        return 1

    # Веб-клиент проверяем компиляцией: живьём его тут не запустить, но именно она
    # ловит, что под него собирается только разрешённое.
    код, текст = конфигуратор("/CheckModules", "-ThinClient", "-WebClient", "-Server",
                              "-ExtendedModulesCheck")
    # Код возврата у проверки модулей ненадёжен: при найденных ошибках он остаётся нулевым,
    # поэтому смотрим на сам протокол - строка с координатами вида {Модуль(89,30)}.
    сорвалась = код != 0 or re.search(r"\{[^}]+\(\d+,\d+\)\}", текст) is not None
    print("проверка модулей: код=%s%s" % (код, ", НАЙДЕНЫ ОШИБКИ" if сорвалась else ""))
    if сорвалась:
        print(текст[:6000])
        return 1
    if текст:
        print(текст[:2000])

    for файл in (ЛОГ, ТРАССА):
        if os.path.exists(файл):
            os.remove(файл)

    if оставить_окно:
        open(ФЛАГ, "w").close()
    elif os.path.exists(ФЛАГ):
        os.remove(ФЛАГ)

    # Гоняем тонкий клиент в строгом режиме - теми же ключами, что включает конфигуратор
    # при отладке. Без них файловые синхронные вызовы проходят, а у пользователя в
    # веб-клиенте или под отладкой падают.
    толстый = "--толстый" in sys.argv
    клиент = платформа() if толстый else платформа("1cv8c.exe")
    запуск = [клиент] + (["ENTERPRISE"] if толстый else []) + [
        "/F" + IB, "/DisableStartupDialogs", "/DisableStartupMessages",
        "/EnableCheckModal", "/EnableCheckSyncCalls", "/EnableCheckExtensionsAndAddInsSyncCalls"]

    часы = time.time()
    процесс = subprocess.Popen(запуск)

    if оставить_окно:
        print("окно предприятия оставлено открытым, жду отчёт...")
        while not os.path.exists(ЛОГ) and time.time() - часы < 180:
            time.sleep(1)
    else:
        try:
            процесс.wait(timeout=180)
        except subprocess.TimeoutExpired:
            процесс.kill()
            print("предприятие не завершилось само - процесс снят")
        print("предприятие: код=%s (%.1f c)" % (процесс.returncode, time.time() - часы))

    print("=" * 70)
    if os.path.exists(ЛОГ):
        print(open(ЛОГ, encoding="utf-8-sig", errors="replace").read())
        return 0

    print("ОТЧЁТ НЕ СОЗДАН:", ЛОГ)
    if os.path.exists(ТРАССА):
        print("трасса прогона:")
        print(open(ТРАССА, encoding="utf-8-sig", errors="replace").read())
    else:
        print("трасса тоже пуста - предприятие оборвалось до первой записи")
    return 1


if __name__ == "__main__":
    sys.exit(main())
