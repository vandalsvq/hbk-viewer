# -*- coding: utf-8 -*-
"""Собирает icons.bsl из svg-файлов каталога icons.

Каждая иконка упаковывается в контейнер картинки 1С: zip с Manifest.xml и вариантами
под разные плотности экрана. Платформа выбирает нужный вариант сама, поэтому в дереве
иконки выглядят резко, а не растянутым одним размером.

Формат контейнера подсмотрен у общих картинок 1С: CommonPictures/*/Picture.zip
в выгрузке конфигурации в файлы.
"""
import base64, io, os, re, zipfile

from стенд import ИСХОДНИКИ

SRC = os.path.join(ИСХОДНИКИ, "icons")
OUT = os.path.join(ИСХОДНИКИ, "icons.bsl")

# Порядок задаёт порядок в модуле; ключ - вид узла оглавления.
ICONS = [
    ("Раздел", "раздел.svg"),
    ("Объект", "объект.svg"),
    ("Метод", "метод.svg"),
    ("Свойство", "свойство.svg"),
    ("Событие", "событие.svg"),
    ("Статья", "статья.svg"),
]

# Масштаб в процентах -> плотность экрана и размер глифа в пикселях.
ВАРИАНТЫ = [
    (85, "bldpi", 14),
    (100, "ldpi", 16),
    (125, "aldpi", 20),
    (150, "mdpi", 24),
    (175, "amdpi", 28),
    (200, "hdpi", 32),
    (300, "xdpi", 48),
    (400, "udpi", 64),
]

HEAD = '''////////////////////////////////////////////////////////////////////////////////
// Иконки дерева содержания. Файл собран из src/icons/*.svg
// генератором icons_to_bsl.py - править нужно svg, а не этот файл.
//
// Каждая картинка - контейнер 1С (zip с Manifest.xml и вариантами под плотности
// экрана), встроенный в код: внешних файлов и макетов обработке не требуется.
////////////////////////////////////////////////////////////////////////////////

// Возвращает картинки видов узлов оглавления.
//
// Возвращаемое значение:
//  Соответствие из КлючИЗначение:
//    * Ключ - Строка - вид узла: Раздел, Объект, Метод, Свойство, Событие, Статья
//    * Значение - Картинка
//
Функция ИконкиУзлов()

\tИконки = Новый Соответствие;

'''

TAIL = '''\tВозврат Иконки;

КонецФункции
'''


def вариант(svg, размер):
    """Тот же рисунок с проставленным размером глифа."""
    def подставить(совпадение):
        тег = совпадение.group(0)
        тег = re.sub(r'\swidth="[^"]*"', '', тег)
        тег = re.sub(r'\sheight="[^"]*"', '', тег)
        return тег[:-1].rstrip() + ' width="%dpx" height="%dpx">' % (размер, размер)

    return re.sub(r"<svg[^>]*>", подставить, svg, count=1)


def контейнер(svg):
    """Картинка 1С: zip с Manifest.xml и вариантами под плотности экрана."""
    строки = ['<?xml version="1.0" encoding="utf-8"?>', "<Picture>"]
    файлы = []

    for масштаб, плотность, размер in ВАРИАНТЫ:
        имя = "%d.svg" % масштаб
        файлы.append((имя, вариант(svg, размер)))
        строки.append('\t<PictureVariant name="%s" screenDensity="%s" isTemplate="false"'
                      ' glyphWidth="%d" glyphHeight="%d"/>' % (имя, плотность, размер, размер))

    # Отдельная строка для интерфейса 8.5 - так же, как в общих картинках платформы.
    строки.append('\t<PictureVariant name="150.svg" screenDensity="mdpi" interfaceVariant="version8_5"'
                  ' isTemplate="false" glyphWidth="24" glyphHeight="24"/>')
    строки.append("</Picture>")

    буфер = io.BytesIO()
    with zipfile.ZipFile(буфер, "w", zipfile.ZIP_DEFLATED) as архив:
        for имя, текст in файлы:
            # Дата фиксирована: иначе icons.bsl меняется при каждой пересборке.
            запись = zipfile.ZipInfo(имя, date_time=(2026, 1, 1, 0, 0, 0))
            запись.compress_type = zipfile.ZIP_DEFLATED
            архив.writestr(запись, "﻿" + текст)
        запись = zipfile.ZipInfo("Manifest.xml", date_time=(2026, 1, 1, 0, 0, 0))
        запись.compress_type = zipfile.ZIP_DEFLATED
        архив.writestr(запись, "﻿" + "\n".join(строки))

    return буфер.getvalue()


def literal(data, indent="\t\t"):
    text = base64.b64encode(data).decode("ascii")
    width = 100
    parts = [text[i:i + width] for i in range(0, len(text), width)]
    lines = ['"%s"' % parts[0]]
    for part in parts[1:]:
        lines.append('%s+ "%s"' % (indent, part))
    return ("\n").join(lines)


def main():
    body = []
    for name, filename in ICONS:
        svg = open(os.path.join(SRC, filename), encoding="utf-8-sig").read()
        body.append('\tИконки.Вставить("%s", Новый Картинка(Base64Значение(\n\t\t%s)));\n'
                    % (name, literal(контейнер(svg))))

    text = HEAD + "\n".join(body) + "\n" + TAIL
    with open(OUT, "wb") as f:
        f.write(text.replace("\n", "\r\n").encode("utf-8"))
    print("icons.bsl:", os.path.getsize(OUT), "байт,", len(ICONS), "иконок по",
          len(ВАРИАНТЫ), "вариантов")


if __name__ == "__main__":
    main()
