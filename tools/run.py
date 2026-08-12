# -*- coding: utf-8 -*-
"""Стенд движка: склейка .bsl -> модуль управляемого приложения тестовой ИБ -> запуск.

    python tools/run.py <файлы .bsl в порядке склейки>
    python tools/run.py tools/test_engine.bsl src/engine_data.bsl src/engine_client.bsl

Гоняет толстым клиентом без строгого режима: здесь меряется движок, а запреты
клиентских синхронных вызовов проверяет tools/build_check.py.
"""
import os, re, subprocess, sys, time

from стенд import РАБОЧИЙ, конфигуратор, платформа, создать_иб

WORK = РАБОЧИЙ
IB = os.path.join(WORK, "ib")
CF = os.path.join(WORK, "cf")
LOG = os.path.join(os.environ.get("TEMP", os.path.expanduser("~")), "spike.log")


def designer(*args):
    return конфигуратор(IB, *args)


def main():
    sources = sys.argv[1:]
    if not sources:
        print(__doc__)
        return 2

    создать_иб(IB)
    if not os.path.exists(os.path.join(CF, "Configuration.xml")):
        print("выгружаю конфигурацию в файлы...")
        designer("/DumpConfigToFiles", CF)

    ext = os.path.join(CF, "Ext")
    os.makedirs(ext, exist_ok=True)
    parts = [open(s, encoding="utf-8-sig").read().replace("\r\n", "\n") for s in sources]
    # Экспортные методы модуля приложения попадают в глобальный контекст и сталкиваются
    # с одноимёнными методами форм той же конфигурации - на стенде экспорт не нужен.
    body = re.sub(r"^((?:Функция|Процедура)\s.*?)\s+Экспорт\s*$", r"\1",
                  "\n\n".join(parts), flags=re.MULTILINE).replace("\n", "\r\n")
    with open(os.path.join(ext, "ManagedApplicationModule.bsl"), "wb") as f:
        f.write(b"\xef\xbb\xbf" + body.encode("utf-8"))

    t = time.time()
    rc, text = designer("/LoadConfigFromFiles", CF)
    print("load config: rc=%s (%.1f c)" % (rc, time.time() - t))
    if rc != 0:
        print(text[:3000])
        return 1

    t = time.time()
    rc, text = designer("/UpdateDBCfg")
    print("update db: rc=%s (%.1f c)" % (rc, time.time() - t))
    if rc != 0:
        print(text[:3000])
        return 1

    rc, text = designer("/CheckModules", "-ThinClient", "-Server")
    if rc != 0 or "(" in text.split("\n")[0]:
        print("СИНТАКСИС:")
        print(text[:4000])
        return 1

    if os.path.exists(LOG):
        os.remove(LOG)

    t = time.time()
    rc = subprocess.call([платформа(), "ENTERPRISE", "/F" + IB,
                          "/DisableStartupDialogs", "/DisableStartupMessages"])
    print("enterprise: rc=%s (%.1f c)" % (rc, time.time() - t))

    print("=" * 60)
    if os.path.exists(LOG):
        print(open(LOG, encoding="utf-8-sig", errors="replace").read())
    else:
        print("ЛОГ НЕ СОЗДАН")
    return 0


if __name__ == "__main__":
    sys.exit(main())
