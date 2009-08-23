#!/usr/bin/env python

# genparser.py file rules tokens [parser.py]

from __future__ import with_statement

import sys
import os.path

sys.path[0] = os.path.abspath(os.path.join(os.path.dirname(__file__),
                                           '..', '..'))
#print "sys.path[0]:", sys.path[0]

from ucc.parser import parser_init, metaparser, metascanner, scanner

def usage():
    sys.stderr.write("usage: genparser.py file rules tokens [parser.py]\n")
    sys.exit(2)

def run():
    if len(sys.argv) != 4 and len(sys.argv) != 5: usage()

    filename = sys.argv[1]
    with open(sys.argv[2]) as f:
        rules = f.read()
    with open(sys.argv[3]) as f:
        token_dict = dict(tuple(line.split()) for line in f)
    if len(sys.argv) == 4:
        genparser(filename, rules, token_dict)
    else:
        with open(sys.argv[4], 'w') as output_file:
            genparser(filename, rules, token_dict, output_file)

def genparser(filename, rules, token_dict, output_file = sys.stdout):
    metaparser.Output_file = output_file
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
        """,
        output_file = output_file)

    for item in sorted(token_dict.iteritems()):
        print >> output_file, "    %r: %r," % item
    print >> output_file, "}\n"

    tokens = sorted(parser_init.parse(metaparser, metascanner, filename,
                                      extra_files = (('rules', rules),))
                     .union(scanner.tokens))

    metaparser.output("""
        def p_error(t):
            if t is None:
                raise SyntaxError("invalid syntax",
                                  scanner_init.syntaxerror_params())
            else:
                raise SyntaxError("invalid syntax",
                                  scanner_init.syntaxerror_params(t))

        """,
        output_file = output_file)

    s = "tokens = %r" % tokens
    i = s.rfind(',', 0, 79)
    while len(s) > 79 and i >= 0:
        print >> output_file, s[:i + 1]
        s = '          ' + s[i + 1:].lstrip()
        i = s.rfind(',', 0, 79)
    print >> output_file, s

    metaparser.output("""

        def init():
            pass

        """,
        output_file = output_file)

if __name__ == "__main__":
    run()
