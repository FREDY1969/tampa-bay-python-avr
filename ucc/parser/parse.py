# parse.py

from __future__ import with_statement

import sys
import os.path

if __name__ == "__main__":
    from doctest_tools import setpath
    setpath.setpath(__file__, remove_first = True)

from ucc.parser import scanner, parser_init
from ucc.ast import ast, crud, symbol_table

def parse_file(parser, kind, filename):
    name, ext = os.path.splitext(os.path.basename(filename))
    assert ext == '.ucl', "unknown file extension on: " + filename

    symbol_id = \
      symbol_table.symbol.create(name, kind, source_filename=filename).id

    args = parser_init.parse(parser, scanner, filename, debug = 0,
                             extra_arg = (symbol_id, parser.token_dict))
    if args is not None:
        with crud.db_transaction():
            ast.save_word(name, symbol_id, args)
        return True, symbol_id
    return False, None

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

