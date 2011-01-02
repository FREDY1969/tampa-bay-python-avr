# word.py

r'''The generic `word` class, along with xml read/write routines for it.

This is one of several representations for a word.  This `word` object is
created by the IDE when a `package` is opened and lives for as long as the
package stays open.  This may encompass several `ucc.compiler.compile` and
`ucc.codegen.load` steps.

This `word` object knows the name (internal name), label (user name), kind
(name of the word that this is a kind of), defining (bool, True if subclass of
declaration, False if instance), `questions` and `answers`, and the location of
the permanent .xml and source files for this word.  The `top_package` object
loads all of the words needed for a package and adds some other attributes to
each word:

    top
      A boolean indicating whether this word is directly in the top-level
      package (the one opened in the IDE) or not.

    kind_obj
      The kind `word` object (whereas 'kind' is just that object's name).
    
    subclasses
      A list of `word` objects that are direct subclasses of this word (only
      defining words have anything here).
      
      This list is sorted by label.lower().
    
    instances
      A list of `word` objects that are direct instances of this word (only
      defining words have anything here).
      
      This list is sorted by label.lower().
    
    filename_suffix
      None or string starting with '.'.  Only set on defining words.

These `word` objects are used by the compiler, along with the subclasses and
instances of the `ucclib.built_in.declaration` class.  The IDE doesn't use the
declaration classes and instances.

'''

import os.path
import itertools
from xml.etree import ElementTree

from ucc.word import answers, questions, xml_access
from ucc.gui import registry

unique = object()

def read_word(word_name, package, top_package):
    r'''Return a single `word` object read in from the word's xml file.
    
    Use `word.save` to write the xml file back out.
    
    '''
    root = ElementTree.parse(os.path.join(package.package_dir,
                                          word_name + '.xml')) \
                      .getroot()
    return from_xml(root, package, top_package)

def from_xml(root, package, top_package):
    name = root.find('name').text
    label = root.find('label').text
    kind = root.find('kind').text
    defining = root.find('defining').text.lower() == 'true'
    answers_element = root.find('answers')
    if not answers_element:
        my_answers = None
    else:
        my_answers = answers.from_xml(answers_element)
    questions_element = root.find('questions')
    if not questions_element:
        my_questions = None
    else:
        my_questions = questions.from_xml(questions_element, top_package)
    return word(package, name, label, defining, kind, my_answers, my_questions)

class word:
    r'''This represents a single generic word.
    
    At this point, this is a one-size-fits-all-kinds-of-words class.
    '''

    def __init__(self, package, name, label, defining, kind,
                 answers = None, questions = None):
        r'''This is called by the `read_word` function.
        
        Or you can call it directly to create a new word.
        
        '''
        
        self.package = package
        self.name = name            # internal name
        self.label = label          # name that user sees
        self.defining = defining    # subclass if True, instance if False
        self.kind = kind            # name of parent word
        self.answers = answers      # {question_name: answers} or None
                                    #   answers can be:
                                    #      - None (unanswered optional)
                                    #      - a single answer object
                                    #   or - a list of answer objects
                                    #        (repetition)
        self.questions = questions  # list of question objects or None.
        
        self.save_state = True
        self.tree_node = None
        self.source_text = None
    
    def __repr__(self):
        return "<{} {}>".format(self.__class__.__name__, self.name)

    def is_root(self):
        r'''Is this word a root word?
        
        A root word is not derived from another word.
        
        '''
        
        return self.kind == self.name
    
    def save(self, package_dir = None):
        r'''Writes the xml file for this word.
        
        The package_dir defaults to the word's package_dir.
        
        '''
        
        xml_access.write_element(self.to_xml(),
                                 os.path.join(package_dir
                                                or self.package.package_dir,
                                              self.name + '.xml'))
        source_filename = self.get_filename()
        if source_filename and registry.rightMainPanel:
            if self.source_text:
                registry.rightMainPanel.bottomText.SetText(self.source_text)
                registry.rightMainPanel.bottomText.SaveFile(source_filename)
        self.set_save_state(True)
    
    def set_save_state(self, state):
        self.save_state = state
        if registry.wordTreeCtrl and self.tree_node:
            registry.wordTreeCtrl.SetItemBold(self.tree_node, not state)
    
    def to_xml(self):
        r'''This generates and returns the xml for the word.
        
        The return value is an ElementTree.Element object.
        
        '''
        
        root = ElementTree.Element('word')
        ElementTree.SubElement(root, 'name').text = self.name
        ElementTree.SubElement(root, 'label').text = self.label
        ElementTree.SubElement(root, 'kind').text = self.kind
        ElementTree.SubElement(root, 'defining').text = str(self.defining)
        answers.add_xml_subelement(root, self.answers)
        questions.add_xml_subelement(root, self.questions)
        return root
    
    def create_question(name):
        # TODO implement method to create a new question of given type
        pass
    
    def delete_question():
        # TODO implement method to delete question and decendent answers
        pass

    def has_questions(self):
        return bool(self.kind_obj.questions)

    def gen_questions(self):
        r'''Generates (question, answer) tuples.

        This includes inherited questions and answers as appropriate (defining
        words inherit answers).

        Each answer can be one of two things:

            An `answer` object
              See `ucc.word.answers` for the possibilities here.
            A list of 0 or more `answer` objects
              for a repeating question

        See also, `get_answer` and `get_value`.

        '''

        for q in self.kind_obj.questions:
            if self.answers:
                yield q, self.get_answer(q.name)
            else:
                yield q, None

    def get_answer(self, question_name, default = unique):
        r'''Return the answer to question_name.

        If this is a defining word, it will check the word's kind for the
        answer if this word doesn't have it.

        If no default parameter is passed, this will raise a KeyError if the
        answer is not found.  Otherwise it will return default.

        An answer can be one of two things:

            An `answer` object
              See `ucc.word.answers` for the possibilities here.
            A list of 0 or more `answer` objects
              for a repeating question

        See also, `gen_questions` and `get_value`.

        '''
        
        if not self.answers or question_name not in self.answers:
            if self.defining:
                try:
                    return self.kind_obj.get_answer(question_name)
                except KeyError:
                    pass
            if default is unique:
                raise KeyError("{}: no answer for {}"
                                 .format(self.label, question_name))
            return default
        return self.answers[question_name]
    
    def set_answer(self, question_name, answer):
        if not self.answers:
            self.answers = {}
        self.answers[question_name] = answer
        self.set_save_state(False)
    
    def get_value(self, question_name, default = None):
        r'''Return the value of the answer to question_name.
        
        If the answer was optional and left unanswered, default is returned.
        
        This is like `get_answer`, but also does the get_value_
        call for you.  If the answer is repeating, it calls get_value on each
        element.
        
        This does not work for series or choice answers.
        
        .. _get_value: ucc.word.answers.answer-class.html#get_value
        
        '''
        
        ans = self.get_answer(question_name)
        if isinstance(ans, answers.answer):
            if not ans.is_answered(): return default
            return ans.get_value()
        return tuple(x.get_value() for x in ans)

    def set_value(self, question_name, answer_value):
        r'''Set the value of the answer to question_name.'''
        self.get_answer(question_name).set_value(answer_value)

    def get_filename(self):
        r'''Returns the complete path to the source file.
        
        Or None if there is no source file for this kind of word.
        
        '''
        
        suffix = self.kind_obj.filename_suffix
        if suffix is None: return None
        return os.path.join(self.package.package_dir, self.name + suffix)

    def has_text(self):
        return self.kind_obj.filename_suffix is not None

    def get_text(self):
        r'''Returns the contents of the source file.

        Or None if there is no source file for this kind of word.
        
        '''
        
        filename = self.get_filename()
        if filename is None: return None
        with open(filename) as f:
            return f.read()

    def write_text(self, text):
        r'''Replaces the contents of the source file.

        raises AssertionError if there is no source file for this kind of word.
        
        '''
        
        filename = self.get_filename()
        if filename is None:
            raise AssertionError(
                    "{}.write_text called for word no source file defined"
                    .format(self.label))
        with open(filename, 'w') as f:
            f.write(text)

