# -*- coding: utf-8 -*-
"""Выгружает собранную обработку в файлы - «разобранный вид» для конфигуратора.

    python tools/dump_epf.py [путь к .epf] [каталог выгрузки]

Нужен тем, у кого нет Python: выгрузка загружается обратно одной командой

    1cv8 DESIGNER /F<ИБ> /LoadExternalDataProcessorOrReportFromFiles
                  dist/выгрузка/ПросмотрСправкиHBK.xml ПросмотрСправкиHBK.epf

Сам по себе каталог выгрузки - результат сборки, править его бесполезно: исходники
лежат в src/, форма собирается formsrc.py.
"""
import os, shutil, subprocess, sys

from стенд import ГОТОВОЕ, РАБОЧИЙ, платформа, создать_иб

ИБ = os.path.join(РАБОЧИЙ, "epf", "ib")

# Корневой XML выгрузки называется по имени объекта метаданных, а не по имени файла .epf.
ИМЯ_ОБЪЕКТА = "ПросмотрСправкиHBK"


def main():
    epf = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ГОТОВОЕ, "hbk-viewer.epf")
    каталог = sys.argv[2] if len(sys.argv) > 2 else os.path.join(ГОТОВОЕ, "выгрузка")

    if not os.path.exists(epf):
        print("нет файла:", epf, "- сначала соберите: python tools/build_epf.py")
        return 1

    создать_иб(ИБ)
    if os.path.isdir(каталог):
        shutil.rmtree(каталог)
    os.makedirs(каталог, exist_ok=True)

    # Платформе передаётся путь корневого XML, а не каталог: рядом с ним она создаёт
    # одноимённый подкаталог с формами и модулями.
    корневой = os.path.join(каталог, ИМЯ_ОБЪЕКТА + ".xml")

    лог = os.path.join(РАБОЧИЙ, "выгрузка.log")
    код = subprocess.call([платформа(), "DESIGNER", "/F" + ИБ,
                           "/DumpExternalDataProcessorOrReportToFiles", корневой, epf,
                           "/Out" + лог, "/DisableStartupDialogs", "/DisableStartupMessages"])
    if код != 0:
        print("выгрузка не удалась, код", код)
        if os.path.exists(лог):
            print(open(лог, encoding="utf-8-sig", errors="replace").read()[:2000])
        return 1

    файлов = sum(len(ф) for _, _, ф in os.walk(каталог))
    print("ГОТОВО:", каталог, "-", файлов, "файлов")
    return 0


if __name__ == "__main__":
    sys.exit(main())
