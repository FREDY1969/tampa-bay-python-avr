# answers.py

r'''Answers to questions.

These are designed to preserve the text that the user typed in to answer the
question.  Thus, they are special answer objects, rather than simple python
types.
'''

from xml.etree import ElementTree

def from_xml(answers_element):
    r'''Returns a dictionary of answers.

    The dictionary keys are the answer names, and the values are either:
        - None -- for an optional answer that wasn't answered
        - a (possibly empty) list of answer objects -- for a repeating answer
        - an answer object -- for a single answer

    This will accept None for answers_element
    '''
    if answers_element is None: return {}
    ans = {}
    for answer in answers_element.getchildren():
        if answer.tag == 'answer':
            name = answer.get('name')
            repeated = answer.get('repeated', 'false').lower() == 'true'
            type = answer.get('type', None)
            if type is None:
                if repeated: ans[name] = []
                else: ans[name] = None
            else:
                value = globals()['ans_' + type].from_element(name, answer)
                if repeated: ans.setdefault(name, []).append(value)
                else: ans[name] = value
        elif answer.tag == 'answers':
            name = answer.get('name')
            repeated = answer.get('repeated', 'false').lower() == 'true'
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

    Expects a dictionary of answers, as returned from from_xml.
    '''
    for name in sorted(answers.keys()):
        value = answers[name]
        if isinstance(value, answer):
            value.add_subelement(answers_element)
        elif not value:
            # value is either None or an empty list.
            ElementTree.SubElement(answers_element, 'answer', name = name,
                                   repeated = str(value is not None))
        else:
            # value is a non-empty list.
            for v in value: v.add_subelement(answers_element, True)

class answer(object):
    r'''Base answer class.

    All answers except omitted answers and lists are (indirect) instances of
    this class.

    The names of all answer subclasses start with 'ans_', for example: ans_bool.
    '''

    def __init__(self, name, value):
        self.name = name
        self.value = value
        assert isinstance(self.value, (str, unicode)), \
               "%s: null value for %s" % (self.__class__.__name__, self.name)

    @classmethod
    def from_element(cls, name, answer):
        return cls(name, get_value_string(name, answer))

    def __repr__(self):
        return "<%s %s=%r>" % (self.__class__.__name__, self.name, self.value)

    def add_subelement(self, answers_element, repeated = False):
        ElementTree.SubElement(answers_element, 'answer', name = self.name,
                               type = self.__class__.__name__[4:],
                               value = self.value, repeated = str(repeated))

    def get_value(self):
        ans = self.convert(self.value)
        #print "answers.get_value", repr(self.value), repr(ans)
        return ans

# These might later convert the answer from a string to the appropriate python
# type.
class ans_bool(answer):
    def convert(self, str):
        if str.lower() == 'true': return True
        if str.lower() == 'false': return False
        raise ValueError("ans_bool %s has invalid value: %s" % (self.name, str))

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

    For example: some_ans_series.subquestion_name => subquestion answer.
    '''

    def __init__(self, name, subanswers = None):
        self.name = name
        self.attributes = subanswers if subanswers is not None else {}
        for name, value in self.attributes.iteritems():
            setattr(self, name, value)

    @classmethod
    def from_element(cls, name, answers):
        return cls(name, from_xml(answers))

    def __repr__(self):
        return "<%s for %s>" % (self.__class__.__name__, self.name)

    def add_subelement(self, answers_element, repeated = False):
        my_answers_element = ElementTree.SubElement(answers_element, 'answers',
                                                    name = self.name,
                                                    repeated = str(repeated))
        add_xml_answers(my_answers_element, self.attributes)

class ans_choice(answer):
    r'''This represents the answer to a question with a list of choices.

    The tag of the choice chosen is some_ans_choice.tag, and the subordinate
    answers (if any) are some_ans_choice.subanswers (as a dict, or None).

    This class is used for questions that only have one choice (single
    selection).  Compare to ans_multichoice.
    '''

    def __init__(self, name, tag, subanswers = None):
        self.name = name
        self.tag = tag
        self.subanswers = subanswers

    @classmethod
    def from_element(cls, name, answer):
        d = parse_options(answer)
        assert len(d) == 1, \
               "%s: expected 1 option to choice, got %d" % (name, len(d))
        return cls(name, *d.items()[0])

    def __repr__(self):
        return "<%s %s=%s->%r>" % (self.__class__.__name__, self.name,
                                   self.tag, self.subanswers)

    def add_subelement(self, answers_element, repeated = False):
        answer_element = ElementTree.SubElement(answers_element, 'answer',
                                                name = self.name,
                                                type =
                                                  self.__class__.__name__[4:],
                                                repeated = str(repeated))
        options_element = ElementTree.SubElement(answer_element, 'options')
        self.add_options(options_element)

    def add_options(self, options_element):
        self.add_option(options_element, self.tag, self.subanswers)

    def add_option(self, options_element, value, subanswers):
        option_element = ElementTree.SubElement(options_element, 'option',
                                                value = str(value))
        add_xml_subelement(option_element, subanswers)

def parse_options(answer):
    r'''Returns dict mapping tag to dict of subanswers (or None).
    '''
    ans = {}
    for option in answer.findall('options/option'):
        value = option.get('value')
        try:
            value = int(value)
        except ValueError:
            pass
        subanswers = from_xml(option.find('answers'))
        ans[value] = subanswers or None
    return ans

class ans_multichoice(ans_choice):
    r'''This represents the answer to a question with a list of choices.

    This class is used for questions that may have multiple choices (multi-
    selection).  Compare to ans_choice.

    The options chosen are in a dictionary accessed through
    some_ans_multichoice.answers.  The keys are the tags, and the values are
    the subordinate answer dictionaries (if any, None otherwise).
    '''

    def __init__(self, name, answers):
        self.name = name
        self.answers = answers

    @classmethod
    def from_element(cls, name, answer):
        return cls(name, parse_options(answer))

    def __repr__(self):
        return "<%s for %s>" % (self.__class__.__name__, self.name)

    def add_options(self, options_element):
        for tag in sorted(self.answers.keys()):
            self.add_option(options_element, tag, self.answers[tag])

def get_value_string(name, answer):
    r'''Looks up the 'value' attribute on the answer tag.

    Raises an exception if the answer tag does not have a 'value' attribute.
    '''
    value_str = answer.get('value')
    if value_str is None:
        raise SyntaxError("%s: missing value for answer" % (name,))
    return value_str

