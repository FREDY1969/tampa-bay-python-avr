# word.py

r'''The generic word class, along with xml read/write routines for it.
'''

from __future__ import with_statement

import os.path

from xml.etree import ElementTree
from ucc.word import answers, questions, xml_access

def read_word(word_name, project_dir):
    r'''Returns a single word object read in from the word's xml file.

    Use word.write_xml to write the xml file back out.
    '''
    tree = ElementTree.parse(os.path.join(project_dir, word_name + '.xml'))
    name = tree.find('name').text
    label = tree.find('label').text
    kind = tree.find('kind').text
    defining = tree.find('defining').text.lower() == 'true'
    answers_element = tree.find('answers')
    if not answers_element:
        answers = None
    else:
        answers = answers.from_xml(answers_element)
    questions_element = tree.find('questions')
    if not questions_element:
        questions = None
    else:
        questions = questions.from_xml(questions_element)
    return word(name, label, defining, kind, answers, questions)

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
        self.answers = answers
        self.questions = questions
    def write_xml(self, project_dir):
        root = ElementTree.Element('word')
        ElementTree.SubElement(root, 'name').text = self.name
        ElementTree.SubElement(root, 'label').text = self.label
        ElementTree.SubElement(root, 'kind').text = self.kind
        ElementTree.SubElement(root, 'defining').text = str(self.defining)
        answers.add_xml_subelement(root, self.answers)
        questions.add_xml_subelement(root, self.questions)
        xml_access.write_element(root,
                                 os.path.join(project_dir, self.name + '.xml'))
    def get_answer(self, question_name):
        return self.answers[question_name]

