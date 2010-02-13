# validators.tst

>>> from xml.etree import ElementTree
>>> from ucc.word import validators, xml_access

>>> root = ElementTree.fromstring('''
... <validation>
...     <validator type="regex" value="[0-9]+$" />
...     <validator type="range" minvalue="2" />
...     <validator type="range" maxvalue="10" />
...     <validator type="range" minvalue="2" maxvalue="10" />
... </validation>
... ''')
>>> v_list = validators.from_xml(root)
>>> v_list
[<regex '[0-9]+$'>, <range 2-None>, <range None-10>, <range 2-10>]

>>> v_list[0].validate('123')
True
>>> v_list[0].validate('123f')
False

>>> v_list[1].validate('123')
True
>>> v_list[1].validate('1')
False

>>> v_list[2].validate('10')
True
>>> v_list[2].validate('11')
False

>>> v_list[3].validate('2')
True
>>> v_list[3].validate('1')
False
>>> v_list[3].validate('10')
True
>>> v_list[3].validate('11')
False

>>> root = ElementTree.Element('validation')
>>> v_list[0].add_xml_subelement(root)
>>> v_list[1].add_xml_subelement(root)
>>> v_list[2].add_xml_subelement(root)
>>> v_list[3].add_xml_subelement(root)
>>> xml_access.indent(root)
>>> print ElementTree.tostring(root)
<validation>
    <validator type="regex" value="[0-9]+$" />
    <validator minvalue="2" type="range" />
    <validator maxvalue="10" type="range" />
    <validator maxvalue="10" minvalue="2" type="range" />
</validation>
<BLANKLINE>
