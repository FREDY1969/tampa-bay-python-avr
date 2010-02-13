# questions.py

r'''The various kinds of questions.

These are all subclasses of the `question` class.
'''

from xml.etree import ElementTree

from ucc.word import validators, answers

def from_xml(questions_element, allow_unknown_tags = False):
    r'''Returns a list of `question` objects.

    This will accept None for the ``questions_element``.
    '''
    if questions_element is None: return []
    ans = []
    for e in questions_element.getchildren():
        if e.tag == 'questions':
            ans.append(q_series.from_element(e))
        elif e.tag == 'question':
            type = e.find('type').text
            cls = globals().get('q_' + type, None)
            if cls is None: raise SyntaxError("unknown question type: " + type)
            ans.append(cls.from_element(e))
        elif not allow_unknown_tags:
            raise SyntaxError("unknown xml tag in <questions>: " + e.tag)
    return ans

def add_xml_subelement(root_element, questions):
    r'''Adds the <questions> tag to root_element if there are any questions.

    Expects a list of questions, as returned from `from_xml`.
    '''
    if questions:
        questions_element = ElementTree.SubElement(root_element, 'questions')
        for q in questions:
            q.add_xml_subelement(questions_element)

class question(object):
    r'''The base class of all questions.
    '''

    tag = 'question'    #: XML tag for this type of question.

    def __init__(self, name, label, min = None, max = None, orderable = None):
        self.name = name
        self.label = label
        self.min = min  # min of None means not optional or repeatable
        self.max = max  # max of None means infinite if min is not None
        self.orderable = orderable
        assert self.is_repeatable() or not self.orderable, \
               "%s: orderable specified on non-repeatable question" % (name,)

    @classmethod
    def from_element(cls, element):
        name = element.find('name').text
        label = element.find('label').text
        min_tag = element.find('min')
        min = int(min_tag.text) if min_tag is not None else None
        max_tag = element.find('max')
        max = None
        if max_tag is not None and max_tag.text.lower() != 'infinite':
            max = int(max_tag.text)
        orderable_tag = element.find('orderable')
        orderable = None
        if orderable_tag is not None:
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

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.name)

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
        return self.orderable == True

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
        ElementTree.SubElement(question, 'type').text = \
          self.__class__.__name__[2:]

    def add_subelements(self, question):
        pass

class q_atomic(question):
    r'''The base class of all atomic questions.

    I.e., questions that have just a single answer (though this answer may be
    optional or repeatable).
    '''

    def __init__(self, name, label, validation = None,
                       min = None, max = None, orderable = None):
        super(q_atomic, self).__init__(name, label, min, max, orderable)
        self.validation = validation

    @classmethod
    def additional_args_from_element(cls, element):
        validation_tag = element.find('validation')
        if validation_tag is None: return {}
        return {'validation': validators.from_xml(validation_tag)}

    def add_subelements(self, question):
        if self.validation:
            validation = ElementTree.SubElement(question, 'validation')
            for v in self.validation: v.add_xml_subelement(validation)

    def make_default_answer(self):
        return self.answer_cls(self.name, self.default_value)

class q_bool(q_atomic):
    answer_cls = answers.ans_bool
    default_value = "False"
    control = 'BoolCtrl'

class q_number(q_atomic):
    answer_cls = answers.ans_number
    default_value = "0"

class q_int(q_atomic):
    answer_cls = answers.ans_int
    default_value = "0"
    control = 'IntegerCtrl'

class q_rational(q_atomic):
    answer_cls = answers.ans_rational
    default_value = "0"

class q_real(q_atomic):
    answer_cls = answers.ans_real
    default_value = "0.0"

class q_string(q_atomic):
    answer_cls = answers.ans_string
    default_value = ""
    control = 'StringCtrl'

class q_series(question):
    r'''A named series of questions.

    The order of the subquestions is the order that the user will see them.
    '''

    tag = 'questions'
    control = 'SeriesCtrl'

    def __init__(self, name, label, subquestions = None,
                       min = None, max = None, orderable = None):
        super(q_series, self).__init__(name, label, min, max, orderable)
        self.subquestions = [] if subquestions is None else list(subquestions)

    @classmethod
    def additional_args_from_element(cls, element):
        return {'subquestions': from_xml(element, allow_unknown_tags = True)}

    def add_type(self, question):
        pass

    def add_subelements(self, question):
        for subq in self.subquestions: subq.add_xml_subelement(question)

    def make_default_answer(self):
        return answers.ans_series(self.name,
                                  dict((q.name, q.make_default_answer())
                                       for q in self.subquestions))


class q_choice(question):
    r'''A question where the user selects one of a set of choices.

    This class covers the single selection choice.  Compare to `q_multichoice`.
    '''

    answer_cls = answers.ans_string
    default_value = ""
    control = 'ChoiceCtrl'

    def __init__(self, name, label, options = None, default = None,
                       min = None, max = None, orderable = None):
        super(q_choice, self).__init__(name, label, min, max, orderable)

        self.options = [] if options is None else list(options) \
          #: list of (name, value, list_of_questions)

        self.default = default

    @classmethod
    def additional_args_from_element(cls, element):
        default_tag = element.find('default')
        default = None if default_tag is None else int(default_tag.text)
        options = []
        for option in element.findall('options/option'):
            options.append((option.get('name'), int(option.get('value')),
                            from_xml(option.find('questions'))))
        return {'options': options, 'default': default}

    def add_subelements(self, question):
        if self.default is not None:
            ElementTree.SubElement(question, 'default').text = str(self.default)
        options = ElementTree.SubElement(question, 'options')
        for name, value, questions in self.options:
            option = ElementTree.SubElement(options, 'option',
                                            name = name, value = str(value))
            add_xml_subelement(option, questions)

    def make_default_answer(self):
        for name, value, subquestions in self.options:
            if value == self.default:
                return answers.ans_choice(self.name,
                                          self.default,
                                          dict((q.name, q.make_default_answer())
                                               for q in subquestions))
        raise AssertionError("q_choice(%s): default, %r, not found in options" %
                               (self.name, self.default))


class q_multichoice(q_choice):
    r'''A question where the user selects from a set of choices.

    This class covers the multiple selection choice.  Compare to `q_choice`.
    '''
    def make_default_answer(self):
        return answers.ans_multichoice(self.name, {})

