#!/usr/bin/env python

# parse.py file...

from __future__ import with_statement

import sys
import os.path

sys.path[0] = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                           '..', '..'))
#print "sys.path[0]:", sys.path[0]

from ucc.parser import scanner, parser_init
from ucc.ast import ast

def usage():
    sys.stderr.write("usage: parse.py file...\n")
    sys.exit(2)

def parse_file(parser, filename):
    name, ext = os.path.splitext(os.path.basename(filename))
    assert ext == '.ucl', "unknown file extension on: " + filename

    root_ast = parser_init.parse(parser, scanner, filename, debug = 0,
                                 extra_arg = parser.token_dict)
    if root_ast:
        root_ast.word = name
        root_ast.str1 = filename
        with ast.db_transaction() as db_cur:
            ast.delete_word_by_name(name)
            id = root_ast.save(db_cur)
        return True, id
    return False, None

def run():
    if len(sys.argv) < 2: usage()

    from ucc.parser import parser

    with ast.db_connection(os.path.dirname(sys.argv[1])):
        num_errors = 0
        for filename in sys.argv[1:]:
            if not parse_file(parser, filename)[0]: num_errors += 1
    if num_errors:
        sys.stderr.write("parse.py: %d files had errors\n" % num_errors)
        sys.exit(1)

if __name__ == "__main__":
    run()

