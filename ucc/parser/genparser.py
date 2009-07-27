#!/usr/bin/python

# genparser.py

from __future__ import with_statement

import sys
import os.path

sys.path[0] = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                           '..', '..'))
#print "sys.path[0]:", sys.path[0]

from ucc.parser import parser_init, metaparser, metascanner, scanner

def usage():
    sys.stderr.write("usage: gen_parser.py file rules tokens > parser.py\n")
    sys.exit(2)

def run():
    if len(sys.argv) != 4: usage()

    metaparser.output("""
        # parser.py

        from ucc.parser import scanner_init
        from ucc.ast import ast

        start = 'file'

        precedence = (
            ('left', 'OR'),
            ('left', 'AND'),
            ('right', 'NOT'),
            ('left', '<', 'LE', 'EQ', 'NE', '>', 'GE'),
            ('left', 'ARG_LEFT_WORD'),
            ('right', 'ARG_RIGHT_WORD'),
            ('left', '+', '-'),
            ('right', '/'),
            ('left', '%'),
            ('left', '*'),
            ('left', 'BIT_OR'),
            ('left', 'BIT_XOR'),
            ('left', 'BIT_AND'),
            ('right', 'NEGATE', 'BIT_NOT'),
            ('left', ')'),
        )

        token_dict = {
        """)

    with open(sys.argv[3]) as f:
        for line in f:
            print "    %r: %r," % tuple(line.split())
        print "}\n"

    tokens = sorted(parser_init.parse(metaparser, metascanner, sys.argv[1],
                                      extra_files = (sys.argv[2],))
                     .union(scanner.tokens))

    metaparser.output("""
        def p_error(t):
            if t is None:
                raise SyntaxError("invalid syntax",
                                  scanner_init.syntaxerror_params())
            else:
                raise SyntaxError("invalid syntax",
                                  scanner_init.syntaxerror_params(t))

        """)

    s = "tokens = %r" % tokens
    i = s.rfind(',', 0, 79)
    while len(s) > 79 and i >= 0:
        print s[:i + 1]
        s = '          ' + s[i + 1:].lstrip()
        i = s.rfind(',', 0, 79)
    print s

    metaparser.output("""

        def init():
            pass

        """)

if __name__ == "__main__":
    run()
