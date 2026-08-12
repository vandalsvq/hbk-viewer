# -*- coding: utf-8 -*-
"""Общее для всех скриптов: где платформа, где исходники, где рабочий каталог.

Ничего машинно-зависимого в остальных скриптах быть не должно - всё здесь.
"""
import glob
import os
import re
import subprocess

TOOLS = os.path.dirname(os.path.abspath(__file__))
КОРЕНЬ = os.path.dirname(TOOLS)
ИСХОДНИКИ = os.path.join(КОРЕНЬ, "src")
ГОТОВОЕ = os.path.join(КОРЕНЬ, "dist")

# Рабочий каталог стендов: одноразовая ИБ и выгрузка конфигурации. Переносить в репозиторий
# нечего, поэтому по умолчанию - временный каталог системы.
РАБОЧИЙ = os.environ.get("HBK_WORK", os.path.join(
    os.environ.get("TEMP", os.path.expanduser("~")), "hbk-viewer"))


def платформа(имя="1cv8.exe"):
    """Путь к исполняемому файлу платформы.

    Порядок: переменная окружения HBK_1C (каталог bin или сам 1cv8.exe), затем самая
    свежая установка из стандартных каталогов. Явная переменная нужна тем, у кого
    платформа стоит не там, где её кладёт установщик.
    """
    указано = os.environ.get("HBK_1C")
    if указано:
        if os.path.isdir(указано):
            путь = os.path.join(указано, имя)
            if os.path.exists(путь):
                return путь
        elif os.path.exists(указано):
            return os.path.join(os.path.dirname(указано), имя)
        raise SystemExit("HBK_1C указывает не на установку платформы: %s" % указано)

    найденные = []
    for корень in (r"C:\Program Files\1cv8", r"C:\Program Files (x86)\1cv8",
                   "/opt/1cv8/x86_64", "/opt/1C/v8.3/x86_64",
                   "/Applications/1cv8.localized"):
        for путь in glob.glob(os.path.join(корень, "*", "bin", имя)):
            найденные.append(путь)
        for путь in glob.glob(os.path.join(корень, имя)):
            найденные.append(путь)

    if not найденные:
        raise SystemExit(
            "Платформа 1С не найдена. Укажите каталог bin в переменной окружения HBK_1C.")

    return max(найденные, key=ключ_версии)


def ключ_версии(путь):
    """Сортировочный ключ по номеру версии в пути: 8.3.27.2214 -> (8, 3, 27, 2214)."""
    найдено = re.search(r"(\d+)\.(\d+)\.(\d+)\.(\d+)", путь)
    return tuple(int(ч) for ч in найдено.groups()) if найдено else (0, 0, 0, 0)


def конфигуратор(ИБ, *аргументы):
    """Запускает пакетный конфигуратор и отдаёт (код возврата, текст протокола)."""
    os.makedirs(РАБОЧИЙ, exist_ok=True)
    выход = os.path.join(РАБОЧИЙ, "designer.log")
    if os.path.exists(выход):
        os.remove(выход)

    код = subprocess.call([платформа(), "DESIGNER", "/F" + ИБ] + list(аргументы) +
                          ["/Out" + выход, "/DisableStartupDialogs", "/DisableStartupMessages"])

    текст = ""
    if os.path.exists(выход):
        # utf-8-sig: конфигуратор пишет протокол с BOM, а он потом ломает вывод в консоль.
        текст = open(выход, encoding="utf-8-sig", errors="replace").read().strip()

    return код, текст


def создать_иб(ИБ):
    """Создаёт пустую файловую ИБ, если её ещё нет."""
    if not os.path.exists(os.path.join(ИБ, "1Cv8.1CD")):
        os.makedirs(ИБ, exist_ok=True)
        subprocess.call([платформа(), "CREATEINFOBASE", "File=" + ИБ,
                         "/DisableStartupDialogs", "/DisableStartupMessages"])
