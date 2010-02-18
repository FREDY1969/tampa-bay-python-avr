# validators.py

r'''These are the various kinds of input validators.

All validators are subclasses of the `validator` class.

'''

import re
from xml.etree import ElementTree

VALIDATOR_TAG = 'validator'     #: XML tag for a validator

def g(): return globals()

def from_xml(root_element):
    r'''Return a list of `validator` objects from an etree node.'''
    ans = []
    for e in root_element.findall(VALIDATOR_TAG):
        type = e.get('type')
        cls = globals().get(type, None)
        if cls is None: raise SyntaxError("unknown validator type: " + type)
        ans.append(cls.from_element(e))
    return ans

class validator(object):
    r'''Base class of all validators.'''
    def add_xml_subelement(self, root_element):
        ElementTree.SubElement(root_element, VALIDATOR_TAG,
                               dict((xml_attr, getattr(self, self_attr)) 
                                    for self_attr, xml_attr in self.xml_mapping
                                    if getattr(self, self_attr, None)
                                         is not None),
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
        flags = element.get('flags')
        return cls(element.get('value'), flags and int(flags))
    
    def __repr__(self):
        return "<%s %r>" % (self.__class__.__name__, self.expr)
    
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
        return cls(element.get('minvalue'), element.get('maxvalue'))
    
    def __repr__(self):
        return "<%s %s-%s>" % (self.__class__.__name__, self.min, self.max)
    
    def validate(self, string):
        n = to_number(string)
        if self.min_n is not None and self.min_n > n: return False
        if self.max_n is not None and self.max_n < n: return False
        return True
    

# FIX: What's the right way to convert numbers for ranges?
def to_number(s):
    return s and int(s)
