# parse.py

from __future__ import with_statement

import sys
import os.path

from ucc.parser import scanner, parser_init

def parse_file(parser, word_word, debug = 0):
    symbol_id = word_word.symbol_id
    filename = word_word.get_filename()

    # Is this really necessary?
    name, ext = os.path.splitext(os.path.basename(filename))
    assert ext == '.ucl', "unknown file extension on: " + filename
    assert name == word_word.name, \
           '%s != %s: internal error' % (name, word_word.name)

    args = parser_init.parse(parser, scanner, filename, debug = debug,
                             extra_arg = (symbol_id, parser.token_dict))
    if args is not None:
        return True, args
    return False, ()

