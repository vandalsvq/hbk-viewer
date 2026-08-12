# -*- coding: utf-8 -*-
"""Сборка внешней обработки просмотрщика справки.

    python tools/build_epf.py [выходной .epf]

Нужна только установленная платформа 1С: сборка идёт пакетным конфигуратором,
EDT и прочие инструменты не участвуют.

XML формы и склейка её модуля живут в formsrc.py - тем же источником пользуется
headless-проверка build_check.py, чтобы форма обработки и проверяемая не разъезжались.
"""
import os, shutil, subprocess, sys, uuid

from formsrc import NS, записать, логформа, модуль_формы, читать
from стенд import ГОТОВОЕ, РАБОЧИЙ, платформа, создать_иб

WORK = os.path.join(РАБОЧИЙ, "epf")
IB = os.path.join(WORK, "ib")
SRC = os.path.join(WORK, "src")
NAME = "ПросмотрСправкиHBK"

ROOT_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<MetaDataObject xmlns="http://v8.1c.ru/8.3/MDClasses" %(ns)s version="2.20">
\t<ExternalDataProcessor uuid="%(u1)s">
\t\t<InternalInfo>
\t\t\t<xr:ContainedObject>
\t\t\t\t<xr:ClassId>c3831ec8-d8d5-4f93-8a22-f9bfae07327f</xr:ClassId>
\t\t\t\t<xr:ObjectId>%(u2)s</xr:ObjectId>
\t\t\t</xr:ContainedObject>
\t\t\t<xr:GeneratedType name="ExternalDataProcessorObject.%(name)s" category="Object">
\t\t\t\t<xr:TypeId>%(u3)s</xr:TypeId>
\t\t\t\t<xr:ValueId>%(u4)s</xr:ValueId>
\t\t\t</xr:GeneratedType>
\t\t</InternalInfo>
\t\t<Properties>
\t\t\t<Name>%(name)s</Name>
\t\t\t<Synonym>
\t\t\t\t<v8:item>
\t\t\t\t\t<v8:lang>ru</v8:lang>
\t\t\t\t\t<v8:content>Просмотр справки 1С</v8:content>
\t\t\t\t</v8:item>
\t\t\t</Synonym>
\t\t\t<Comment/>
\t\t\t<DefaultForm>ExternalDataProcessor.%(name)s.Form.Форма</DefaultForm>
\t\t\t<AuxiliaryForm/>
\t\t</Properties>
\t\t<ChildObjects>
\t\t\t<Form>Форма</Form>
\t\t</ChildObjects>
\t</ExternalDataProcessor>
</MetaDataObject>
'''

FORM_MD_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<MetaDataObject xmlns="http://v8.1c.ru/8.3/MDClasses" %(ns)s version="2.20">
\t<Form uuid="%(u5)s">
\t\t<Properties>
\t\t\t<Name>Форма</Name>
\t\t\t<Synonym>
\t\t\t\t<v8:item>
\t\t\t\t\t<v8:lang>ru</v8:lang>
\t\t\t\t\t<v8:content>Справка 1С</v8:content>
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
\t</Form>
</MetaDataObject>
'''


def main():
    выход = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ГОТОВОЕ, NAME + ".epf")
    os.makedirs(os.path.dirname(выход), exist_ok=True)

    создать_иб(IB)

    if os.path.isdir(SRC):
        shutil.rmtree(SRC)

    d = {"ns": NS, "name": NAME}
    for i in range(1, 6):
        d["u%d" % i] = str(uuid.uuid4())

    записать(os.path.join(SRC, NAME + ".xml"), ROOT_XML % d)
    записать(os.path.join(SRC, NAME, "Ext", "ObjectModule.bsl"), читать("object_module.bsl"))
    записать(os.path.join(SRC, NAME, "Forms", "Форма.xml"), FORM_MD_XML % d)
    записать(os.path.join(SRC, NAME, "Forms", "Форма", "Ext", "Form.xml"), логформа(NAME))
    записать(os.path.join(SRC, NAME, "Forms", "Форма", "Ext", "Form", "Module.bsl"), модуль_формы())

    лог = os.path.join(WORK, "load.log")
    if os.path.exists(выход):
        os.remove(выход)
    код = subprocess.call([платформа(), "DESIGNER", "/F" + IB,
                           "/LoadExternalDataProcessorOrReportFromFiles",
                           os.path.join(SRC, NAME + ".xml"), выход, "/Out" + лог,
                           "/DisableStartupDialogs", "/DisableStartupMessages"])
    print("load exit:", код)
    if os.path.exists(лог):
        print(open(лог, encoding="utf-8", errors="replace").read().strip()[:3000])
    if os.path.exists(выход):
        print("ГОТОВО:", выход, os.path.getsize(выход), "байт")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
