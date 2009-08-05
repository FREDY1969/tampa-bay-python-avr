# xml_access.py

r'''Routines to read and write the xml files.

The routines for reading an individual word are in word.py.
'''

from __future__ import with_statement

import os.path

from xml.etree import ElementTree

Packages_filename = 'packages.xml'
Package_filename = 'package.xml'

def read_package_list(packages_dir):
    r'''Returns the list of package names read from the packages.xml file.

    Use write_package_list to write the xml file back out.
    '''
    tree = ElementTree.parse(os.path.join(packages_dir, Packages_filename))
    return [e.get('name') for e in tree.getiterator('package')]

def write_package_list(package_list, packages_dir):
    r'''Writes a list of package names to the packages.xml file.

    Sorts the names to reduce merge conflicts.
    '''
    root = ElementTree.Element('packages')
    for name in sorted(package_list):
        ElementTree.SubElement(root, 'package', name = name)
    write_element(root, os.path.join(packages_dir, Packages_filename))

def read_word_list(project_dir):
    r'''Returns the project_name and list of word names for the project.

    Read from the 'package.xml' file.

    Use write_word_list to write the xml file back out.
    '''
    tree = ElementTree.parse(os.path.join(project_dir, Package_filename))
    return (tree.find('name').text,
            [e.get('name') for e in tree.getiterator('word')])

def write_word_list(package_name, word_list, project_dir):
    r'''Writes the project_name and list of word names to the package.xml file.

    Sorts the names to reduce merge conflicts.
    '''
    root = ElementTree.Element('package')
    ElementTree.SubElement(root, 'name').text = package_name
    words = ElementTree.SubElement(root, 'words')
    for name in sorted(word_list):
        ElementTree.SubElement(words, 'word', name = name)
    write_element(root, os.path.join(project_dir, Package_filename))

def write_element(root, filename):
    r'''Writes root element to filename with pretty indenting.
    '''
    indent(root)
    with open(filename, 'w') as xml_file:
        xml_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        ElementTree.ElementTree(root).write(xml_file, 'utf-8')

def indent(element, level = 0, amount = 4):
    r'''Adds pretty indenting to element and all of its children.

    It does this by adding a newline and spaces to the 'text' and 'tail'
    attributes of the elements.  The 'text' string is what is between the open
    tag and the first child tag.  The 'tail' string is what is between the
    closing tag and the next sibling.
    '''
    children = element.getchildren()
    if children:
        level += 1
        element.text = '\n' + ' ' * (level * amount)
        for child in children: indent(child, level, amount)
        level -= 1
        children[-1].tail = '\n' + ' ' * (level * amount)
    element.tail = '\n' + ' ' * (level * amount)