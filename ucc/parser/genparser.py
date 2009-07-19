#!/usr/bin/python

# genparser.py

import sys
import os.path

sys.path[0] = os.path.abspath(os.path.join('..', '..',
                                           os.path.dirname(__file__)))
#print "sys.path:", sys.path

from ucc.parser import parser_init, metaparser, metascanner, scanner

def usage():
    sys.stderr.write("usage: gen_parser.py file\n")
    sys.exit(2)

def run():
    if len(sys.argv) != 2: usage()

    print """# parser.py

start = 'file'

precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('right', 'NOT'),
    ('left', '<', 'LE', 'EQ', 'NE', '>', 'GE'),
    ('left', 'ARG_LEFT_WORD'),
    ('right', 'ARG_RIGHT_WORD'),
    ('left', '+', '-'),
    ('right', '/', '%'),
    ('left', '*'),
    ('left', 'BIT_OR'),
    ('left', 'BIT_XOR'),
    ('left', 'BIT_AND'),
    ('right', 'NEGATE', 'BIT_NOT'),
    ('left', ')'),
)"""

    tokens = sorted(parser_init.parse(metaparser, metascanner, sys.argv[1])
                     .union(scanner.tokens))

    print
    s = "tokens = %r" % tokens
    i = s.rfind(',', 0, 79)
    while len(s) > 79 and i >= 0:
        print s[:i + 1]
        s = '          ' + s[i + 1:].lstrip()
        i = s.rfind(',', 0, 79)
    print s

if __name__ == "__main__":
    run()
