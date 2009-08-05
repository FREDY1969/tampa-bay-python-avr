# questions.py

from xml.etree import ElementTree

def from_xml(questions_element):
    r'''Returns a list of question objects.
    '''
    ans = []
    for e in questions_element.getchildren():
        if e.tag == 'questions':
            ans.append(series.from_element(e))
        elif e.tag == 'question':
            type = e.find('type').text
            cls = getattr(globals(), type, None)
            if cls is None: raise SyntaxError("unknown question type: " + type)
            ans.append(cls.from_element(e))
    return ans

class question(object):
    tag = 'question'
    def __init__(self, name, label, min = None, max = None, orderable = None):
        self.name = name
        self.label = label
        self.min = min  # min of None means not optional or repeatable
        self.max = max  # max of None means infinite if min is not None
        self.orderable = orderable
    @classmethod
    def from_element(cls, element):
        name = element.find('name').text
        label = element.find('label').text
        min_tag = element.find('min')
        min = int(min_tag.text) if min_tag is not None else None
        max_tag = element.find('max')
        max = None
        if max_tag and max_tag.text.lower() != 'infinite':
            max = int(max_tag.text)
        orderable_tag = element.find('orderable')
        orderable = None
        if orderable_tag:
            if orderable_tag.text.lower() == 'false': orderable = False
            elif orderable_tag.text.lower() == 'true': orderable = True
            else:
                raise SyntaxError("question %s: illegal orderable value, %r" %
                                    (name, orderable_tag.text))
        rest_args = cls.additional_args_from_element(element)
        return cls(name = name, label = label,
                   min = min, max = max, orderable = orderable, **rest_args)
    @classmethod
    def additional_args_from_element(cls, element):
        return {}
    def is_optional(self):
        r'''Returns True or False.
        '''
        return self.min == 0 and self.max == 1
    def is_repeatable(self):
        r'''Returns (min, max) or False.

        Max is None if infinite.
        '''
        if self.min is None: return False
        if self.max == 1: # either optional or self.min == 1 too.
            return False
        return (self.min, self.max)
    def is_orderable(self):
        r'''Returns True or False.
        '''
        return self.orderable and self.is_repeatable()
    def add_xml_subelement(self, root_element):
        question = ElementTree.SubElement(root_element, self.tag)
        ElementTree.SubElement(question, 'name').text = self.name
        ElementTree.SubElement(question, 'label').text = self.label
        if self.min is not None:
            ElementTree.SubElement(question, 'min').text = str(self.min)
            ElementTree.SubElement(question, 'max').text = \
              'infinite' if self.max is None \
                         else str(self.max)
            if self.is_repeatable():
                ElementTree.SubElement(question, 'orderable').text = \
                  str(self.is_orderable())
        self.add_type(question)
        self.add_subelements(question)
    def add_type(self, question):
        ElementTree.SubElement(question, 'type').text = self.__class__.__name__
    def add_subelements(self, question):
        pass

class atomic(question):
    def __init__(self, name, label, validation = None,
                       min = None, max = None, orderable = None):
        super(atomic, self).__init__(name, label, min, max, orderable)
        self.validation = validation
    @classmethod
    def additional_args_from_element(cls, element):
        validation_tag = element.find('validation')
        if validation_tag is None: return {}
        return {'validation': [validators.from_xml(v)
                               for v in validation_tag.findall('validator')]}
    def add_subelements(self, question):
        if self.validation:
            validation = ElementTree.SubElement(question, 'validation')
            for v in self.validation: v.add_xml_subelement(validation)

class bool(atomic):
    pass

class number(atomic):
    pass

class int(atomic):
    pass

class rational(atomic):
    pass

class real(atomic):
    pass

class string(atomic):
    pass

class series(question):
    tag = 'questions'
    def __init__(self, name, label, subquestions = None,
                       min = None, max = None, orderable = None):
        super(atomic, self).__init__(name, label, min, max, orderable)
        self.subquestions = [] if subquestions is None else list(subquestions)
    @classmethod
    def additional_args_from_element(cls, element):
        return {'subquestions': from_xml(element)}
    def add_type(self, question):
        pass
    def add_subelements(self, question):
        for subq in self.subquestions: subq.add_xml_subelement(question)

class choice(question):
    def __init__(self, name, label, options = None, default = None,
                       min = None, max = None, orderable = None):
        super(choice, self).__init__(name, label, min, max, orderable)

        # self.options is list of (name, value, question)
        self.options = [] if options is None else list(options)
        self.default = default
    @classmethod
    def additional_args_from_element(cls, element):
        default_tag = element.find('default')
        default = None if default_tag is None else int(default_tag.text)
        options = []
        for option in element.find('options/option'):
            options.append((option.get('name'), int(option.get('value')),
                            from_xml(option)))
        return {'options': options, 'default': default}
    def add_subelements(self, question):
        if self.default is not None:
            ElementTree.SubElement(question, 'default').text = str(self.default)
        options = ElementTree.SubElement(question, 'options')
        for name, value, question in self.options:
            option = ElementTree.SubElement(options, 'option',
                                            name = name, value = str(value))
            question.add_xml_subelement(option)

class multichoice(choice):
    pass
