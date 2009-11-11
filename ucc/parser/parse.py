# parse.py

from __future__ import with_statement

import sys
import os.path

if __name__ == "__main__":
    from doctest_tools import setpath
    setpath.setpath(__file__, remove_first = True)

from ucc.parser import scanner, parser_init
from ucc.ast import ast, crud

def parse_file(parser, word_word):
    symbol_id = word_word.symbol_id
    filename = word_word.get_filename()

    # Is this really necessary?
    name, ext = os.path.splitext(os.path.basename(filename))
    assert ext == '.ucl', "unknown file extension on: " + filename
    assert name == word_word.name, \
           '%s != %s: internal error' % (name, word_word.name)

    args = parser_init.parse(parser, scanner, filename, debug = 0,
                             extra_arg = (symbol_id, parser.token_dict))
    if args is not None:
        with crud.db_transaction():
            ast.save_word(word_word.label, symbol_id, args)
        return True
    return False

def usage():
    sys.stderr.write("usage: python parse.py file...\n")
    sys.exit(2)

def run():
    if len(sys.argv) < 2: usage()

    from ucc.parser import parser

    with crud.db_connection(os.path.dirname(sys.argv[1])):
        num_errors = 0
        for filename in sys.argv[1:]:
            if not parse_file(parser, filename)[0]: num_errors += 1
    if num_errors:
        sys.stderr.write("parse.py: %d files had errors\n" % num_errors)
        sys.exit(1)

if __name__ == "__main__":
    run()

