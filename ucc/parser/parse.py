# parse.py

from __future__ import with_statement

import sys
import os.path

if __name__ == "__main__":
    from doctest_tools import setpath
    setpath.setpath(__file__, remove_first = True)

from ucc.parser import scanner, parser_init
from ucc.ast import ast

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

def usage():
    sys.stderr.write("usage: python parse.py file...\n")
    sys.exit(2)

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

