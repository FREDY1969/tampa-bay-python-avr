# word.py

r'''The generic word class, along with xml read/write routines for it.
'''

from __future__ import with_statement

import os.path
from xml.etree import ElementTree

import setpath
setpath.setpath(__file__)

from ucc.word import answers, questions, xml_access

def read_word(word_name, project_dir):
    r'''Returns a single word object read in from the word's xml file.
    
    Use word.write_xml to write the xml file back out.
    '''
    root = ElementTree.parse(os.path.join(project_dir, word_name + '.xml')) \
                      .getroot()
    return from_xml(root)

def from_xml(root):
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
    return word(name, label, defining, kind, my_answers, my_questions)

class word(object):
    r'''This represents a single generic word.

    At this point, this is a one-size-fits-all-kinds-of-words class.
    '''

    def __init__(self, name, label, defining, kind,
                 answers = None, questions = None):
        self.name = name
        self.label = label
        self.defining = defining
        self.kind = kind
        self.answers = answers      # {question_name: answers}
                                    #   answers can be:
                                    #      - None (unanswered optional)
                                    #      - a single answer object
                                    #   or - a list of answer objects
                                    #        (repetition)
        self.questions = questions  # list of question objects.

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, self.name)

    def write_xml(self, project_dir):
        xml_access.write_element(self.to_xml(),
                                 os.path.join(project_dir, self.name + '.xml'))

    def to_xml(self):
        root = ElementTree.Element('word')
        ElementTree.SubElement(root, 'name').text = self.name
        ElementTree.SubElement(root, 'label').text = self.label
        ElementTree.SubElement(root, 'kind').text = self.kind
        ElementTree.SubElement(root, 'defining').text = str(self.defining)
        answers.add_xml_subelement(root, self.answers)
        questions.add_xml_subelement(root, self.questions)
        return root

    def get_answer(self, question_name):
        return self.answers[question_name]

