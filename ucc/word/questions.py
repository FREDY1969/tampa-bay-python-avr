# questions.py

r'''The various kinds of questions.

These are all subclasses of the `question` class.

'''

from xml.etree import ElementTree

from ucc.word import validators, answers

def from_xml(questions_element, top_package, allow_unknown_tags = False):
    r'''Return a list of `question` objects from a questions etree node.
    
    This will accept None for the ``questions_element``.
    
    '''
    if questions_element is None: return []
    ans = []
    for e in questions_element.getchildren():
        if e.tag == 'questions':
            ans.append(q_series.from_element(e, top_package))
        elif e.tag == 'question':
            type = e.find('type').text
            cls = globals().get('q_' + type, None)
            if cls is None: raise SyntaxError("unknown question type: " + type)
            ans.append(cls.from_element(e, top_package))
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

class question:
    r'''The base class of all questions.'''
    
    tag = 'question'    #: XML tag for this type of question.
    
    def __init__(self, name, label, min = None, max = None, orderable = None):
        self.name = name
        self.label = label
        self.min = min  # min of None means not optional or repeatable
        self.max = max  # max of None means infinite if min is not None
        self.orderable = orderable
        assert self.is_repeatable() or not self.orderable, \
               "{}: orderable specified on non-repeatable question".format(name)

    @classmethod
    def from_element(cls, element, top_package):
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
                raise SyntaxError("question {}: illegal orderable value, {!r}"
                                    .format(name, orderable_tag.text))
        rest_args = cls.additional_args_from_element(element, top_package)
        return cls(name = name, label = label,
                   min = min, max = max, orderable = orderable, **rest_args)

    @classmethod
    def additional_args_from_element(cls, element, top_package):
        return {}

    @classmethod
    def from_answer(cls, name, label, min, max, orderable, type_subanswers,
                         top_package):
        rest_arg = cls.additional_args_from_subanswers(type_subanswers,
                                                       top_package)
        return cls(name = name, label = label,
                   min = min, max = max, orderable = orderable, **rest_args)

    @classmethod
    def additional_args_from_subanswers(cls, subanswers, top_package):
        return {}

    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, self.name)

    def is_optional(self):
        r'''Returns True or False.'''
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
        r'''Returns True or False.'''
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
    def additional_args_from_element(cls, element, top_package):
        validation_tag = element.find('validation')
        if validation_tag is None: return {}
        return {'validation': validators.from_xml(validation_tag)}
    
    def add_subelements(self, question):
        if self.validation:
            validation = ElementTree.SubElement(question, 'validation')
            for v in self.validation: v.add_xml_subelement(validation)
    
    def make_default_answer(self):
        return self.answer_cls(self.name, self.default_value)

    def layout(self):
        return 'atomic'

class q_bool(q_atomic):
    answer_cls = answers.ans_bool
    default_value = "False"
    control = 'BoolCtrl'

class q_number(q_atomic):
    answer_cls = answers.ans_number
    default_value = "0"
    control = 'StringCtrl'

class q_int(q_atomic):
    answer_cls = answers.ans_int
    default_value = "0"
    control = 'IntegerCtrl'

class q_rational(q_atomic):
    answer_cls = answers.ans_rational
    default_value = "0"
    control = "RationalCtrl"

class q_real(q_atomic):
    answer_cls = answers.ans_real
    default_value = "0.0"
    control = "RealCtrl"

class q_string(q_atomic):
    answer_cls = answers.ans_string
    default_value = ""
    control = 'NumberCtrl'

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
    def additional_args_from_element(cls, element, top_package):
        return {'subquestions': from_xml(element, top_package,
                                         allow_unknown_tags = True)}

    @classmethod
    def additional_args_from_subanswers(cls, subanswers, top_package):
        return {'subquestions':
                  [as_question(a, top_package) for a in subanswers.subquestion],
               }

    def add_type(self, question):
        pass
    
    def add_subelements(self, question):
        for subq in self.subquestions: subq.add_xml_subelement(question)
    
    def make_default_answer(self):
        return answers.ans_series(self.name,
                                  {q.name: q.make_default_answer()
                                   for q in self.subquestions})

    def gen_subquestions(self, answer):
        return ((q, answer and getattr(answer, q.name))
                for q in self.subquestions)

    def layout(self):
        if len(self.subquestions) < 4 and \
           all(q.layout() == 'atomic' and 
                 not q.is_repeatable() and
                 not q.is_optional()
               for q in self.subquestions):
            return 'simple_series'
        return 'series'


class q_choice(question):
    r'''A question where the user selects one of a set of choices.
    
    This class covers the single selection choice.  Compare to `q_multichoice`.
    
    '''

    answer_cls = answers.ans_string
    default_value = ""
    control = 'ChoiceCtrl'
    input_type = 'radio'

    def __init__(self, name, label, options = None, default = None,
                       min = None, max = None, orderable = None):
        super(q_choice, self).__init__(name, label, min, max, orderable)

        self.options = [] if options is None else list(options) \
          #: list of (name, value, list_of_questions)

        self.default = default

    @classmethod
    def additional_args_from_element(cls, element, top_package):
        default_tag = element.find('default')
        default = None if default_tag is None \
                       else answers.convert_tag(default_tag.text)
        options = []
        for option in element.findall('options/option'):
            options.append((option.get('name'),
                            answers.convert_tag(option.get('value')),
                            from_xml(option.find('questions'), top_package)))
        return {'options': options, 'default': default}

    @classmethod
    def additional_args_from_subanswers(cls, subanswers, top_package):
        return {'options':
                  [cls.option_from_answer(a, top_package)
                   for a in subanswers.q_options],
                'default': None,
               }

    @classmethod
    def option_from_answer(cls, answer, top_package):
        return (answer.label.value, answer.value.value,
                [as_question(a, top_package) for a in answer.subquestions])

    @classmethod
    def choose_choice(cls, name, label, min, max, orderable, type_subanswers,
                           top_package):
        if type_subanswers.multiple.value:
            return q_multichoice.from_answer(name, label, min, max, orderable,
                                             type_subanswers, top_package)
        else:
            return q_choice.from_answer(name, label, min, max, orderable,
                                        type_subanswers, top_package)

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
                                          {q.name: q.make_default_answer()
                                           for q in subquestions})
        raise AssertionError("q_choice({}): default, {!r}, not found in options"
                               .format(self.name, self.default))

    def gen_subquestions(self, option, answer):
        opt_name, opt_value, opt_subquestions = option
        if answer and answer.subanswers and answer.tag == opt_value:
            return ((q, answer.subanswers[q.name])
                    for q in (opt_subquestions or ()))
        return ((q, None) for q in (opt_subquestions or ()))

    def layout(self):
        if all(len(q) == 0 for _, _, q in self.options):
            return 'simple_choice'
        return 'choice'


class q_multichoice(q_choice):
    r'''A question where the user selects from a set of choices.
    
    This class covers the multiple selection choice.  Compare to `q_choice`.
    
    '''
    
    control = 'MultiChoiceCtrl'
    input_type = 'checkbox'
    
    def make_default_answer(self):
        return answers.ans_multichoice(self.name, {})

    def gen_subquestions(self, option, answer):
        opt_name, opt_value, opt_subquestions = option
        if answer and answer.answers and answer.answers.get(opt_value):
            return ((q, answer.answers[opt_value][q.name])
                    for q in (opt_subquestions or ()))
        return ((q, None) for q in (opt_subquestions or ()))

    def layout(self):
        return 'choice'


class q_indirect(question):
    r'''This is an indirect reference to a question defined as a word.
    '''

    def __init__(self, name, label, use, top_package,
                       min = None, max = None, orderable = None):
        super(q_indirect, self).__init__(name, label, min, max, orderable)
        assert use, "Indirect question {}: missing 'use' argument".format(name)
        self.use = use
        self.real_question = None
        self.top_package = top_package

    @classmethod
    def additional_args_from_element(cls, element, top_package):
        use = element.find('use').text
        return {'use': use, 'top_package': top_package}

    @classmethod
    def additional_args_from_subanswers(cls, subanswers, top_package):
        return {'use': subanswers.question_name,
                'top_package': top_package,
               }

    def add_subelements(self, question):
        ElementTree.SubElement(question, 'use').text = self.use

    def __getattr__(self, name):
        return getattr(self.get_real_question(), name)

    def get_real_question(self):
        if self.real_question is None:
            use_word = self.top_package.get_word_by_label(self.use)
            if use_word.defining:
                # kludge to let the built_in "question" word refer to itself:
                assert use_word.name == 'question'
                self.real_question = use_word.questions[0]
            else:
                if not hasattr(use_word, 'answer_as_question'):
                    use_word.answer_as_question = \
                      as_question(use_word.get_answer('question'),
                                  self.top_package)
                self.real_question = use_word.answer_as_question
        return self.real_question

Type_to_question_class = {
      'bool': q_bool.from_answer,
      'int': q_int.from_answer,
      'rational': q_rational.from_answer,
      'real': q_real.from_answer,
      'string': q_string.from_answer,
      'series': q_series.from_answer,
      'choice': q_choice.choose_choice,
      'indirect': q_indirect.from_answer,
  }

def as_question(ans, top_package):
    label = ans.q_label.value
    name = ans.q_name.value
    modifier = ans.modifier.tag
    if modifier == 'required':
        min = 1
        max = 1
        orderable = None
    elif modifier == 'optional':
        min = 0
        max = 1
        orderable = None
    elif modifier == 'repeated':
        subanswers = ans.modifier.subanswers
        a = subanswers.q_min
        min = a.value if a.is_answered() else None
        a = subanswers.q_max
        if not a.is_answered() or a.value == 'infinite':
            max = None
        else:
            max = a.value
        orderable = subanswers.q_orderable.value
    else:
        raise ValueError(
                'unknown modifier for indirect question {}'.format(label))
    type = ans.type.tag
    return Type_to_question_class[type](name, label, min, max, orderable,
                                        ans.type.subanswers, top_package)
