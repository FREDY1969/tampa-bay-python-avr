# word.py

r'''The generic `word` class, along with xml read/write routines for it.

This is one of several representations for a word.  This `word` object is
created by the IDE when a `package` is opened and lives for as long as the
package stays open.  This may encompass several `ucc.parser.compile` and
`ucc.parser.load` steps.

This `word` object knows the name (internal name), label (user name), kind
(name of the word that this is a kind of), defining (bool, True if subclass of
declaration, False if instance), `questions` and `answers`, and the location of
the permanent .xml and source files for this word.  The `top_package` object
loads all of the words needed for a package and adds some other attributes to
each word:

    top
      A boolean indicating whether this word is directly in the top-level
      package (the one opened in the IDE) or not.

    package_name
      The full dotted module name of the `package` containing this word.
      This is set by the `package.package` object.

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

from __future__ import with_statement

import os.path
import itertools
from xml.etree import ElementTree

from ucc.word import answers, questions, xml_access

unique = object()

def read_word(word_name, package_dir):
    r'''Returns a single `word` object read in from the word's xml file.
    
    Use `word.write_xml` to write the xml file back out.
    '''
    #print "read_word", word_name
    root = ElementTree.parse(os.path.join(package_dir, word_name + '.xml')) \
                      .getroot()
    return from_xml(root, package_dir)

def from_xml(root, package_dir):
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
        my_questions = questions.from_xml(questions_element)
    return word(package_dir, name, label, defining, kind, my_answers,
                my_questions)

class word(object):
    r'''This represents a single generic word.

    At this point, this is a one-size-fits-all-kinds-of-words class.
    '''

    def __init__(self, package_dir, name, label, defining, kind,
                 answers = None, questions = None):
        r'''This is called by the `read_word` function.

        Or you can call it directly to create a new word.
        '''
        self.package_dir = package_dir
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

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.name)

    def is_root(self):
        r'''Is this word a root word?

        A root word is not derived from another word.
        '''
        return self.kind == self.name

    def write_xml(self, package_dir = None):
        r'''Writes the xml file for this word.

        The package_dir defaults to the word's package_dir.
        '''
        xml_access.write_element(self.to_xml(),
                                 os.path.join(package_dir or self.package_dir,
                                              self.name + '.xml'))

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

    def get_answer(self, question_name, default = unique):
        r'''Return the answer to question_name.

        If this is a defining word, it will check the word's kind for the
        answer if this word doesn't have it.

        If no default parameter is passed, this will raise a KeyError if the
        answer is not found.  Otherwise it will return default.

        An answer can be one of three things:

            None
              for an optional answer that was left unanswered
            An `answer` object
              See `ucc.word.answers` for the possibilities here.
            A list of 0 or more `answer` objects
              for a repeating question

        See also, `get_value`.
        '''
        if not self.answers or question_name not in self.answers:
            if self.defining:
                try:
                    return self.kind_obj.get_answer(question_name)
                except KeyError:
                    pass
            if default is unique:
                raise KeyError("%s: no answer for %s" %
                                 (self.label, question_name))
            return default
        return self.answers[question_name]

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
        if ans is None: return default
        if isinstance(ans, answers.answer): return ans.get_value()
        return tuple(itertools.imap(lambda x: x.get_value(), ans))

    def get_filename(self):
        r'''Returns the complete path to the source file.

        Or None if there is no source file for this kind of word.
        '''
        suffix = self.kind_obj.filename_suffix
        if suffix is None: return None
        return os.path.join(self.package_dir, self.name + suffix)

    def set_answer(self, question_name, answer):
        if not self.answers or question_name not in self.answers:
            raise KeyError("%s: no answer for %s" % (self.label, question_name))
        self.answers[question_name] = answer
