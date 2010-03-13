# questions.tst

>>> from xml.etree import ElementTree
>>> from ucc.word import questions, xml_access

>>> root = ElementTree.fromstring('''
... <questions>
...     <question>
...         <name>q1</name>
...         <label>Q1</label>
...         <type>bool</type>
...     </question>
...     <question>
...         <name>q2</name>
...         <label>Q2</label>
...         <type>number</type>
...         <min>0</min>
...         <orderable>False</orderable>
...     </question>
...     <question>
...         <name>q3</name>
...         <label>Q3</label>
...         <type>int</type>
...         <min>0</min>
...         <orderable>True</orderable>
...     </question>
...     <question>
...         <name>q4</name>
...         <label>Q4</label>
...         <type>rational</type>
...         <min>0</min>
...         <max>1</max>
...     </question>
...     <question>
...         <name>q5</name>
...         <label>Q5</label>
...         <type>real</type>
...         <min>1</min>
...         <max>infinite</max>
...         <orderable>False</orderable>
...     </question>
...     <question>
...         <name>q6</name>
...         <label>Q6</label>
...         <type>string</type>
...         <min>1</min>
...         <max>3</max>
...         <orderable>True</orderable>
...     </question>
... </questions>
... ''')
>>> q_list = questions.from_xml(root)
>>> q_list
[<q_bool q1>, <q_number q2>, <q_int q3>, <q_rational q4>, <q_real q5>, <q_string q6>]

>>> q_list[0].is_optional()
False
>>> q_list[0].is_repeatable()
False
>>> q_list[0].is_orderable()
False

>>> q_list[1].is_optional()
False
>>> q_list[1].is_repeatable()
(0, None)
>>> q_list[1].is_orderable()
False

>>> q_list[2].is_optional()
False
>>> q_list[2].is_repeatable()
(0, None)
>>> q_list[2].is_orderable()
True

>>> q_list[3].is_optional()
True
>>> q_list[3].is_repeatable()
False
>>> q_list[3].is_orderable()
False

>>> q_list[4].is_optional()
False
>>> q_list[4].is_repeatable()
(1, None)
>>> q_list[4].is_orderable()
False

>>> q_list[5].is_optional()
False
>>> q_list[5].is_repeatable()
(1, 3)
>>> q_list[5].is_orderable()
True

>>> root = ElementTree.Element('questions')
>>> q_list[0].add_xml_subelement(root)
>>> q_list[1].add_xml_subelement(root)
>>> q_list[2].add_xml_subelement(root)
>>> q_list[3].add_xml_subelement(root)
>>> q_list[4].add_xml_subelement(root)
>>> q_list[5].add_xml_subelement(root)
>>> xml_access.indent(root)
>>> print(ElementTree.tostring(root))
<questions>
    <question>
        <name>q1</name>
        <label>Q1</label>
        <type>bool</type>
    </question>
    <question>
        <name>q2</name>
        <label>Q2</label>
        <min>0</min>
        <max>infinite</max>
        <orderable>False</orderable>
        <type>number</type>
    </question>
    <question>
        <name>q3</name>
        <label>Q3</label>
        <min>0</min>
        <max>infinite</max>
        <orderable>True</orderable>
        <type>int</type>
    </question>
    <question>
        <name>q4</name>
        <label>Q4</label>
        <min>0</min>
        <max>1</max>
        <type>rational</type>
    </question>
    <question>
        <name>q5</name>
        <label>Q5</label>
        <min>1</min>
        <max>infinite</max>
        <orderable>False</orderable>
        <type>real</type>
    </question>
    <question>
        <name>q6</name>
        <label>Q6</label>
        <min>1</min>
        <max>3</max>
        <orderable>True</orderable>
        <type>string</type>
    </question>
</questions>
<BLANKLINE>

>>> root = ElementTree.fromstring('''
... <questions>
...     <question>
...         <name>q1</name>
...         <label>Q1</label>
...         <type>choice</type>
...         <options>
...             <option name="HIGH" value="1" />
...             <option name="LOW" value="0">
...                 <questions>
...                     <question>
...                         <name>sure</name>
...                         <label>Are you sure?</label>
...                         <type>bool</type>
...                     </question>
...                 </questions>
...             </option>
...         </options>
...     </question>
...     <question>
...         <name>q2</name>
...         <label>Q2</label>
...         <type>choice</type>
...         <default>1</default>
...         <options>
...             <option name="HIGH" value="1" />
...             <option name="LOW" value="0">
...                 <questions>
...                     <question>
...                         <name>sure</name>
...                         <label>Are you sure?</label>
...                         <type>bool</type>
...                     </question>
...                 </questions>
...             </option>
...         </options>
...     </question>
...     <question>
...         <name>q3</name>
...         <label>Q3</label>
...         <type>multichoice</type>
...         <options>
...             <option name="HIGH" value="1" />
...             <option name="LOW" value="0">
...                 <questions>
...                     <question>
...                         <name>sure</name>
...                         <label>Are you sure?</label>
...                         <type>bool</type>
...                     </question>
...                 </questions>
...             </option>
...         </options>
...     </question>
...     <question>
...         <name>q4</name>
...         <label>Q4</label>
...         <type>multichoice</type>
...         <default>1</default>
...         <options>
...             <option name="HIGH" value="1" />
...             <option name="LOW" value="0">
...                 <questions>
...                     <question>
...                         <name>sure</name>
...                         <label>Are you sure?</label>
...                         <type>bool</type>
...                     </question>
...                     <questions>
...                         <name>s1</name>
...                         <label>S1</label>
...                         <min>1</min>
...                         <max>1</max>
...                         <orderable>False</orderable>
...                         <question>
...                             <name>sq1</name>
...                             <label>SQ1</label>
...                             <type>int</type>
...                         </question>
...                         <question>
...                             <name>sq2</name>
...                             <label>SQ2</label>
...                             <type>string</type>
...                         </question>
...                     </questions>
...                 </questions>
...             </option>
...         </options>
...     </question>
... </questions>
... ''')
>>> q_list = questions.from_xml(root)
>>> q_list
[<q_choice q1>, <q_choice q2>, <q_multichoice q3>, <q_multichoice q4>]

>>> q_list[0].default
>>> q_list[0].options
[('HIGH', 1, []), ('LOW', 0, [<q_bool sure>])]

>>> q_list[1].default
1
>>> q_list[1].options
[('HIGH', 1, []), ('LOW', 0, [<q_bool sure>])]

>>> q_list[2].default
>>> q_list[2].options
[('HIGH', 1, []), ('LOW', 0, [<q_bool sure>])]

>>> q_list[3].default
1
>>> q_list[3].options
[('HIGH', 1, []), ('LOW', 0, [<q_bool sure>, <q_series s1>])]

>>> s = q_list[3].options[1][2][1]
>>> s
<q_series s1>
>>> s.min
1
>>> s.max
1
>>> s.subquestions
[<q_int sq1>, <q_string sq2>]

>>> root = ElementTree.Element('questions')
>>> q_list[0].add_xml_subelement(root)
>>> q_list[1].add_xml_subelement(root)
>>> q_list[2].add_xml_subelement(root)
>>> q_list[3].add_xml_subelement(root)
>>> xml_access.indent(root)
>>> print(ElementTree.tostring(root))
<questions>
    <question>
        <name>q1</name>
        <label>Q1</label>
        <type>choice</type>
        <options>
            <option name="HIGH" value="1" />
            <option name="LOW" value="0">
                <questions>
                    <question>
                        <name>sure</name>
                        <label>Are you sure?</label>
                        <type>bool</type>
                    </question>
                </questions>
            </option>
        </options>
    </question>
    <question>
        <name>q2</name>
        <label>Q2</label>
        <type>choice</type>
        <default>1</default>
        <options>
            <option name="HIGH" value="1" />
            <option name="LOW" value="0">
                <questions>
                    <question>
                        <name>sure</name>
                        <label>Are you sure?</label>
                        <type>bool</type>
                    </question>
                </questions>
            </option>
        </options>
    </question>
    <question>
        <name>q3</name>
        <label>Q3</label>
        <type>multichoice</type>
        <options>
            <option name="HIGH" value="1" />
            <option name="LOW" value="0">
                <questions>
                    <question>
                        <name>sure</name>
                        <label>Are you sure?</label>
                        <type>bool</type>
                    </question>
                </questions>
            </option>
        </options>
    </question>
    <question>
        <name>q4</name>
        <label>Q4</label>
        <type>multichoice</type>
        <default>1</default>
        <options>
            <option name="HIGH" value="1" />
            <option name="LOW" value="0">
                <questions>
                    <question>
                        <name>sure</name>
                        <label>Are you sure?</label>
                        <type>bool</type>
                    </question>
                    <questions>
                        <name>s1</name>
                        <label>S1</label>
                        <min>1</min>
                        <max>1</max>
                        <question>
                            <name>sq1</name>
                            <label>SQ1</label>
                            <type>int</type>
                        </question>
                        <question>
                            <name>sq2</name>
                            <label>SQ2</label>
                            <type>string</type>
                        </question>
                    </questions>
                </questions>
            </option>
        </options>
    </question>
</questions>
<BLANKLINE>
