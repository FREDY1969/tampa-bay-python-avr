# validators.py

import re
from xml.etree import ElementTree

Validator_tag = 'validator'

def from_xml(root_element):
    r'''Returns a list of validator objects.
    '''
    ans = []
    for e in root_element.findall(Validator_tag):
        type = e.get('type')
        cls = getattr(globals(), type, None)
        if cls is None: raise SyntaxError("unknown validator type: " + type)
        ans.append(cls.from_element(e))
    return ans

class validator(object):
    def add_xml_subelement(self, root_element):
        return ElementTree.SubElement(root_element, Validator_tag,
                                      dict((xml_attr, getattr(self, self_attr)) 
                                           for self_attr, xml_attr
                                            in self.xml_mapping),
                                      type = self.__class__.__name__)

class regex(validator):
    xml_mapping = (('expr',  'value'), ('flags', 'flags'))
    def __init__(self, expr, flags = None):
        self.expr = expr
        self.flags = flags
        self.re = re.compile(expr) if flags is None \
                                   else re.compile(expr, flags)
    @classmethod
    def from_element(cls, element):
        return cls(element.get('value'), int(element.get('flags')))
    def validate(self, string):
        match = self.re.match(string)
        return match is not None

class range(validator):
    xml_mapping = (('min', 'minvalue'), ('max', 'maxvalue'))
    def __init__(self, min, max):
        self.min = min
        self.max = max
        self.min_n = to_number(min)
        self.max_n = to_number(max)
    @classmethod
    def from_element(cls, element):
        return cls(int(element.get('minvalue')), int(element.get('maxvalue')))
    def validate(self, string):
        return self.min_n <= to_number(string) <= self.max_n
