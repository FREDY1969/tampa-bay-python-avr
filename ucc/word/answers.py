# answers.py

r'''Answers to `questions`.

These are designed to preserve the text that the user typed in to answer the
`questions.question`.  Thus, they are special answer objects, rather than
simple python types.

They are stored in xml format to be able to track and merge in source code
control systems.

Answer series use an "answers" tag, all other answers use an "answer" tag.

All answers (including series) have 'name' and 'repeated' attributes.
Repeated answers are represented as multiple xml elements with the same name.
If a repeating answer has zero answers, a single xml element with null="True"
is used as a placeholder for the empty list.  In this case, there is no type
attribute.

Optional answers that are left unanswered also have the null="True" attribute
and have no 'value' attribute.  But they have repeated="False" (since repeating
answers can't be optional since you can just have zero repetitions).

All answers, except series, also have a 'type' attribute, which matches one of
the ans_X classes defined in this module.

Both series and choices have subordinate answers as nested (child) xml
elements.  All other answers have a 'value' attribute with the answer to the
question (unless the null="True" attribute is set).
'''

from xml.etree import ElementTree

def from_xml(answers_element):
    r'''Return a dictionary of `answer` objects from an answers etree node.
    
    The dictionary keys are the answer names, and the values are either:
    
        An `answer` object
          for a single answer
        A (possibly empty) list of `answer` objects
          for a repeating answer

    This will accept None for answers_element
    
    '''
    
    if answers_element is None: return {}
    ans = {}
    for answer in answers_element.getchildren():
        if answer.tag == 'answer':
            name = answer.get('name')
            repeated = answer.get('repeated', 'false').lower() == 'true'
            type = answer.get('type', None)
            if answer.get('null', 'false').lower() == 'true': 
                if repeated: 
                    ans[name] = []
                else:
                    ans[name] = globals()['ans_' + type].create_unanswered(name)
            else:
                value = globals()['ans_' + type].from_element(name, answer)
                if repeated: ans.setdefault(name, []).append(value)
                else: ans[name] = value
        elif answer.tag == 'answers':
            name = answer.get('name')
            repeated = answer.get('repeated', 'false').lower() == 'true'
            if answer.get('null', 'false').lower() == 'true': 
                if repeated: 
                    ans[name] = []
                else:
                    ans[name] = ans_series.create_unanswered(name)
            else:
                value = ans_series.from_element(name, answer)
                if repeated: ans.setdefault(name, []).append(value)
                else: ans[name] = value
        else:
            raise SyntaxError("unknown xml tag in <answers>: " + answer.tag)
    return ans

def add_xml_subelement(root_element, answers):
    r'''Adds the <answers> tag to root_element if there are any answers.
    
    Expects a dictionary of answers, as returned from from_xml.
    '''
    
    if answers:
        answers_element = ElementTree.SubElement(root_element, 'answers')
        add_xml_answers(answers_element, answers)

def add_xml_answers(answers_element, answers):
    r'''Fills in the <answers> tag.
    
    Expects a dictionary of answers, as returned from `from_xml`.
    
    '''
    
    for name in sorted(answers.keys()):
        value = answers[name]
        if isinstance(value, answer):
            # This takes care of the unanswered case too.
            value.add_subelement(answers_element)
        elif not value:
            # value is an empty list.
            ElementTree.SubElement(answers_element, 'answer', name = name,
                                   repeated = 'True', null = 'True')
        else:
            # value is a non-empty list.
            for v in value: v.add_subelement(answers_element, True)

class answer:
    r'''Base answer class.

    All answers except omitted answers and lists are (indirect) instances of
    this class.

    The names of all answer subclasses start with ``ans_``, for example:
    `ans_bool`.

    '''

    def __init__(self, name, value = None, answered = True):
        self.name = name
        self.value = value
        self.valid = True
        self.answered = answered
        assert not self.answered or isinstance(self.value, str), \
               "{}: {} value for {}".format(self.__class__.__name__,
                                            type(self.value),
                                            self.name)

    @classmethod
    def from_element(cls, name, answer):
        return cls(name, answer.get('value'))

    @classmethod
    def create_unanswered(cls, name):
        return cls(name, answered = False)

    @classmethod
    def from_value(cls, name, value):
        try:
            ans = cls(name, value)
            ans.get_value()
        except ValueError:
            ans.value = ''
            ans.valid = False
        return ans

    def __repr__(self):
        if self.is_answered():
            return "<{} {}={!r}>".format(self.__class__.__name__, self.name,
                                         self.value)
        return "<{} {} unanswered>".format(self.__class__.__name__, self.name)

    def is_answered(self):
        return self.answered

    def unanswer(self):
        self.answered = False

    def set_answer(self, value):
        self.answered = True
        self.value = value
        try:
            self.get_value()
        except ValueError:
            self.value = ''
            self.valid = False

    def add_subelement(self, answers_element, repeated = False):
        if self.is_answered():
            ElementTree.SubElement(answers_element, 'answer', name = self.name,
                                   type = self.__class__.__name__[4:],
                                   value = self.value, repeated = str(repeated))
        else:
            ElementTree.SubElement(answers_element, 'answer', name = self.name,
                                   type = self.__class__.__name__[4:],
                                   null = 'True', repeated = str(repeated))

    def get_value(self):
        if not self.is_answered():
            raise AttributeError("answer {}: unanswered".format(self.name))
        return self.convert(self.value)


# These might later convert the answer from a string to the appropriate python
# type.
class ans_bool(answer):
    def convert(self, str):
        if str.lower() == 'true': return True
        if str.lower() == 'false': return False
        raise ValueError("ans_bool {} has invalid value: {}".format(self.name, 
                                                                    str))

class ans_number(answer):
    def convert(self, str):
        try:
            return int(str)
        except ValueError:
            return float(str)

class ans_int(answer):
    convert = lambda self, s: int(s, 0)

class ans_rational(answer):
    def convert(self, str):
        raise AssertionError("ans_rational.convert not implemented")

class ans_real(answer):
    convert = float

class ans_string(answer):
    convert = lambda self, x: x

class ans_series(answer):
    r'''This handles a nested <answers> tag represented a series of answers.
    
    The individual answers can be accessed as attributes on this object.
    
    For example::
    
        some_ans_series.subquestion_name => subquestion_answer.
    
    '''
    
    def __init__(self, name, subanswers = None, answered = True):
        self.name = name
        self.answered = answered
        self.attributes = subanswers if subanswers is not None else {}
        for name, value in self.attributes.items():
            setattr(self, name, value)

    @classmethod
    def from_element(cls, name, answers):
        return cls(name, from_xml(answers))

    def __repr__(self):
        return "<{} for {}>".format(self.__class__.__name__, self.name)

    def add_subelement(self, answers_element, repeated = False):
        if self.is_answered():
            my_answers_element = \
              ElementTree.SubElement(answers_element, 'answers',
                                     name = self.name, repeated = str(repeated))
            add_xml_answers(my_answers_element, self.attributes)
        else:
            my_answers_element = \
              ElementTree.SubElement(answers_element, 'answers',
                                     name = self.name,
                                     repeated = str(repeated),
                                     null = 'True')


class ans_choice(answer):
    r'''This represents the `answer` to a `question` with a list of choices.
    
    The tag of the choice chosen is some_ans_choice.tag, and the subordinate
    answers (if any) are some_ans_choice.subanswers (as a dict, or None).
    
    This class is used for questions that only have one choice (single
    selection).  Compare to ans_multichoice.
    
    '''
    
    def __init__(self, name, tag = None, subanswers = None, answered = True):
        self.name = name
        self.answered = answered
        if self.answered:
            self.tag = tag
            self.subanswers = subanswers

    @classmethod
    def from_element(cls, name, answer):
        d = parse_options(answer)
        assert len(d) == 1, \
               "{}: expected 1 option to choice, got {}".format(name, len(d))
        return cls(name, *list(d.items())[0])

    def __repr__(self):
        if self.is_answered():
            return "<{} {}={}->{!r}>".format(self.__class__.__name__, self.name,
                                             self.tag, self.subanswers)
        return "<{} {} unanswered>".format(self.__class__.__name__, self.name)

    def add_subelement(self, answers_element, repeated = False):
        if self.is_answered():
            answer_element = \
              ElementTree.SubElement(answers_element, 'answer',
                                     name = self.name,
                                     type = self.__class__.__name__[4:],
                                     repeated = str(repeated))
            options_element = ElementTree.SubElement(answer_element, 'options')
            self.add_options(options_element)
        else:
            answer_element = \
              ElementTree.SubElement(answers_element, 'answer',
                                     name = self.name,
                                     type = self.__class__.__name__[4:],
                                     repeated = str(repeated),
                                     null = 'True')

    def add_options(self, options_element):
        self.add_option(options_element, self.tag, self.subanswers)
    
    def add_option(self, options_element, value, subanswers):
        option_element = ElementTree.SubElement(options_element, 'option',
                                                value = str(value))
        add_xml_subelement(option_element, subanswers)
    

def parse_options(answer):
    r'''Returns dict mapping tag to dict of subanswers (or None).'''
    ans = {}
    for option in answer.findall('options/option'):
        tag = convert_tag(option.get('value'))
        subanswers = from_xml(option.find('answers'))
        ans[tag] = subanswers or None
    return ans

def convert_tag(value):
    r'''Attempts to convert value to an int.
    
    If the conversion fails, value is returned unmolested.

        >>> convert_tag('44')
        44
        >>> convert_tag('44g')
        '44g'
    '''
    try:
        return int(value)
    except ValueError:
        return value

class ans_multichoice(ans_choice):
    r'''This represents the `answer` to a `question` with a list of choices.
    
    This class is used for questions that may have multiple choices (multi-
    selection).  Compare to `ans_choice`.

    The options chosen are in a dictionary accessed through
    some_ans_multichoice.answers.  The keys are the tags, and the values are
    the subordinate answer dictionaries (if any, None otherwise).

    '''

    def __init__(self, name, answers = None, answered = True):
        self.name = name
        self.answered = answered
        if self.answered:
            self.answers = answers

    @classmethod
    def from_element(cls, name, answer):
        return cls(name, parse_options(answer))
    
    def __repr__(self):
        return "<{} for {}>".format(self.__class__.__name__, self.name)

    def add_options(self, options_element):
        for tag in sorted(self.answers.keys()):
            self.add_option(options_element, tag, self.answers[tag])

