# -*- coding: utf-8 -*-
"""Забирает разметку формы из собранной обработки обратно в исходники.

    python import_form.py [путь к .epf]

Форму удобнее править в конфигураторе, поэтому дорога в обе стороны:
build_epf.py собирает обработку из form_layout.xml, а этот скрипт возвращает
изменённую разметку назад. Реквизит с основным объектом заменяется подстановкой -
у общей формы стенда его быть не должно.

Модуль формы сюда не возвращается: он собирается из .bsl-файлов. Если модуль в
обработке разошёлся с исходниками, скрипт об этом скажет.
"""
import os, shutil, subprocess, sys

from formsrc import записать, модуль_формы
from стенд import ГОТОВОЕ, ИСХОДНИКИ, РАБОЧИЙ, платформа

WORK = os.path.join(РАБОЧИЙ, "epf")
IB = os.path.join(WORK, "ib")
ВЫГРУЗКА = os.path.join(WORK, "импорт")
РАЗМЕТКА = os.path.join(ИСХОДНИКИ, "form_layout.xml")


def main():
    epf = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ГОТОВОЕ, "hbk-viewer.epf")
    if not os.path.exists(epf):
        print("нет файла:", epf)
        return 1

    if os.path.isdir(ВЫГРУЗКА):
        shutil.rmtree(ВЫГРУЗКА)

    лог = os.path.join(WORK, "импорт.log")
    код = subprocess.call([платформа(), "DESIGNER", "/F" + IB,
                           "/DumpExternalDataProcessorOrReportToFiles", ВЫГРУЗКА, epf,
                           "/Out" + лог, "/DisableStartupDialogs", "/DisableStartupMessages"])
    if код != 0:
        print("выгрузка не удалась, код", код)
        if os.path.exists(лог):
            print(open(лог, encoding="utf-8", errors="replace").read()[:2000])
        return 1

    корень = os.path.join(ВЫГРУЗКА, "Forms", "Форма", "Ext")
    разметка = open(os.path.join(корень, "Form.xml"), encoding="utf-8-sig").read()

    # Реквизит основного объекта есть только у формы обработки - выносим в подстановку.
    начало = разметка.find('\t\t<Attribute name="Объект"')
    if начало < 0:
        print("в форме нет реквизита Объект - это не форма внешней обработки")
        return 1
    конец = разметка.find("\t\t</Attribute>\n", начало) + len("\t\t</Attribute>\n")
    разметка = разметка[:начало] + "%(объект)s" + разметка[конец:]

    записать(РАЗМЕТКА, разметка)
    print("разметка обновлена:", РАЗМЕТКА)

    в_обработке = open(os.path.join(корень, "Form", "Module.bsl"), encoding="utf-8-sig").read()
    if в_обработке.replace("\r\n", "\n").rstrip() != модуль_формы().replace("\r\n", "\n").rstrip():
        print("ВНИМАНИЕ: модуль формы в обработке отличается от собранного из .bsl.")
        print("Правки кода из обработки не переносятся - перенести вручную в исходники.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
