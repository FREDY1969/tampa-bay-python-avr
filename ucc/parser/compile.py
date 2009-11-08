#!/usr/bin/env python

# compile.py package_dir

from __future__ import with_statement

import sys
import os, os.path
import contextlib
import itertools
import traceback
import sqlite3 as db
from doctest_tools import setpath

if __name__ == "__main__":
    setpath.setpath(__file__, remove_first = True)

from ucc.word import helpers, xml_access, word
from ucc.parser import genparser
from ucc.ast import ast
from ucc.assembler import assemble

Built_in = 'ucclib.built_in'

def run(top):

    # The following gets a little confusing because we have two kinds of word
    # objects:
    #
    #   1.  word_word objects (instances of the ucc.word.word.word class)
    #   2.  word_obj objects (either subclasses or instances of the
    #                         ucclib.built_in.declaration.declaration class)
    #

    ast.Translation_dict = top.translation_dict

    # Gather word_objs_by_name, and build the parsers for each package:
    word_objs_by_name = {}   # {word.name: word_obj}
    rules = []
    token_dict = {}
    # Load words:
    def load_word(word_word):
        if word_word.name not in word_objs_by_name:
            if not word_word.is_root() and \
               word_word.kind not in word_objs_by_name:
                load_word(top.get_word_by_name(word_word.kind))

            if word_word.is_root():
                mod = helpers.import_module(word_word.package_name + 
                                              '.' + word_word.name)
                new_word = getattr(mod, word_word.name)
                new_syntax = new_word.init_class(word_word.name, word_word.name,
                                                 word_word.package_dir)
            else:
                new_word, new_syntax = \
                  word_objs_by_name[word_word.kind] \
                    .create_instance(word_word.package_name, word_word.name,
                                     word_word.label, word_word.package_dir)
            if new_syntax:
                r, td = new_syntax
                rules.extend(r)
                token_dict.update(td)
            word_objs_by_name[word_word.name] = new_word

    package_parsers = {}        # {package_name: parser module}
    syntax_file = os.path.join(os.path.dirname(__file__), 'SYNTAX')
    for p in top.packages:
        for word_word in p.get_words():
            load_word(word_word)

        #print "rules", rules
        #print "token_dict", token_dict

        # compile new parser for this package:
        with open(os.path.join(p.package_dir, 'parser.py'), 'w') as output_file:
            genparser.genparser(syntax_file, '\n'.join(rules), token_dict,
                                output_file)

        # import needed modules from the package:
        package_parsers[p.package_name] = \
          helpers.import_module(p.package_name + '.parser')

    # parse files in the package:
    num_errors = 0
    with ast.db_connection(top.packages[-1].package_dir):
        for name, word_obj in word_objs_by_name.iteritems():
            #print "final loop", name, word_obj
            try:
                if not isinstance(word_obj, type): # word_obj not a class
                    word_word = top.get_word_by_name(name)
                    word_obj.parse_file(package_parsers[word_word.package_name],
                                        word_word.package_dir)
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
        with open(os.path.join(top.packages[-1].package_dir, 'flash.hex'),
                  'w') \
          as flash_file:
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
    sys.stderr.write("usage: compile.py package_dir\n")
    sys.exit(2)

if __name__ == "__main__":
    if len(sys.argv) != 2: usage()
    from ucc.word import top_package

    run(top_package.top(sys.argv[1]))
