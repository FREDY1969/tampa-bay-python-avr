#!/usr/bin/env python

# compile.py package_name

from __future__ import with_statement

import sys
import os, os.path
import contextlib
import itertools
import traceback
import sqlite3 as db

if __name__ == "__main__":
    from doctest_tools import setpath

    setpath.setpath(__file__, remove_first = True)

from ucc.word import helpers, xml_access, word
from ucc.parser import genparser
from ucc.ast import ast
from ucc.assembler import assemble

Built_in = 'ucclib.built_in'

def run(package_name):

    # Figure out package directories.
    package_dir = os.path.split(helpers.import_module(package_name).__file__)[0]
    built_in_dir = os.path.split(helpers.import_module(Built_in).__file__)[0]

    # Get the list of word_names.
    #   This is actually a list of (package_name, package_dir, word_name).
    def get_names(package_name, dir):
        return map(lambda name: (package_name, dir, name),
                   xml_access.read_word_list(dir)[1])
    word_names = get_names(Built_in, built_in_dir) + \
                 get_names(package_name, package_dir)

    # The following gets a little confusing because we have two kinds of word
    # objects:
    #
    #   1.  word_word objects (instances of the ucc.word.word.word class)
    #   2.  word_obj objects (either subclasses or instances of the
    #                         ucclib.built_in.declaration.declaration class)
    #

    # Load word.word objects and create translation_dict:
    word_words = {}             # {word.name: word.word object}
    translation_dict = {}       # {word.label: word.name}
    for pkg_name, dir, name in word_names:
        word_obj = word.read_word(name, dir)
        word_obj.package_name = pkg_name
        assert word_obj.name not in word_words, \
               "%s: duplicate word name: %s" % (word_obj.label, word_obj.name)
        word_words[word_obj.name] = word_obj
        if word_obj.name != word_obj.label:
            assert word_obj.label not in translation_dict, \
                   "%s: duplicate word" % word_obj.label
            translation_dict[word_obj.label] = word_obj.name

    ast.Translation_dict = translation_dict

    # Gather word_objs_by_name, rules and token_dict:
    mod = helpers.import_module(Built_in + '.declaration')
    decl = getattr(mod, 'declaration')
    decl.init_class('declaration', 'declaration', built_in_dir)
    word_objs_by_name = {'declaration': decl}   # {word.name: word_obj}
    rules = []
    token_dict = {}
    # Load words:
    def load_word(word_word):
        if word_word.name not in word_objs_by_name:
            if word_word.kind not in word_objs_by_name:
                load_word(word_words[word_word.kind])

            new_word, new_syntax = \
              word_objs_by_name[word_word.kind] \
                .create_instance(word_word.package_name, word_word.name,
                                 word_word.label, word_word.package_dir)
            if new_syntax:
                r, td = new_syntax
                rules.extend(r)
                token_dict.update(td)
            word_objs_by_name[word_word.name] = new_word

    for word_word in word_words.itervalues():
        load_word(word_word)

    #print "rules", rules
    #print "token_dict", token_dict

    # compile new parser for this package:
    with open(os.path.join(package_dir, 'parser.py'), 'w') as output_file:
        genparser.genparser(os.path.join(os.path.dirname(__file__), 'SYNTAX'),
                            '\n'.join(rules), token_dict, output_file)

    # import needed modules from the package:
    parser = helpers.import_module(package_name + '.parser')

    # parse files in the package:
    num_errors = 0
    with ast.db_connection(package_dir):
        for name, word_obj in word_objs_by_name.iteritems():
            #print "final loop", name, word_obj
            try:
                if not isinstance(word_obj, type): # word_obj not a class
                    word_obj.parse_file(parser, word_words[name].package_dir)
            except SyntaxError:
                e_type, e_value, e_tb = sys.exc_info()
                for line in traceback.format_exception_only(e_type, e_value):
                    sys.stderr.write(line)
                num_errors += 1
            except Exception:
                traceback.print_exc()
                num_errors += 1
        if num_errors:
            sys.stderr.write("%s files had syntax errors\n" % num_errors)
            sys.exit(1)

        flash = []      # list of (label, opcode, operand1, operand2)
        data = []       # list of (label, datatype, operand)
        bss = []        # list of (label, num_bytes)
        eeprom = []     # list of (label, datatype, operand)
        words_done = set()
        words_needed = set(['startup'])
        while words_needed:
            next_word = words_needed.pop()
            with ast.db_transaction() as db_cur:
                f, d, b, e, n = \
                  word_objs_by_name[next_word].compile(db_cur,
                                                       word_objs_by_name)
            flash.extend(f)
            data.extend(d)
            bss.extend(b)
            eeprom.extend(e)
            words_done.add(next_word)
            words_needed.update(frozenset(n) - words_done)
        #print "flash", flash
        #print "data", data
        #print "bss", bss
        #print "eeprom", eeprom
        with open(os.path.join(package_dir, 'flash.hex'), 'w') as flash_file:
            insts = assemble.assemble(flash)
            for i in itertools.count():
                data_hex = ''.join(itertools.imap(
                                     lambda n: "%04x" % byte_reverse(n),
                                     itertools.islice(insts, 8)))
                if not data_hex: break
                line = "%02x%04x00%s" % (len(data_hex)/2, i * 16, data_hex)
                flash_file.write(":%s%02x\r\n" % (line, check_sum(line)))
                if len(data_hex) < 32: break
            assert not data
            assert not bss
            flash_file.write(":00000001FF\r\n")
        assert not eeprom

def byte_reverse(n):
    r'''Reverses the two bytes in a 16 bit number.

    >>> hex(byte_reverse(0x1234))
    '0x3412'
    '''
    return ((n << 8) & 0xff00) | (n >> 8)

def check_sum(data):
    r'''Calculates the .hex checksum.

    >>> hex(check_sum('100000000C9445010C9467110C9494110C946D01'))
    '0x9f'
    >>> hex(check_sum('10008000202D2068656C70202874686973206F75'))
    '0x56'
    '''
    sum = 0
    for i in range(0, len(data), 2):
        sum += int(data[i:i+2], 16)
    return (256 - (sum & 0xff)) & 0xFF

def usage():
    sys.stderr.write("usage: compile.py package_name\n")
    sys.exit(2)

if __name__ == "__main__":
    if len(sys.argv) != 2: usage()

    run(sys.argv[1])
