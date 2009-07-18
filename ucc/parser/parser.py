# parser.py

""" See http://www.dabeaz.com/ply/ply.html for syntax of grammer definitions.
""" 

from __future__ import with_statement
from ucc.parser import scanner, scanner_init

tokens = scanner.tokens

def p_file(t):
    r''' file :
    '''
    pass

def p_error(t):
    if t is None:
        raise SyntaxError("invalid syntax", scanner_init.syntaxerror_params())
    else:
        raise SyntaxError("invalid syntax", scanner_init.syntaxerror_params(t))

