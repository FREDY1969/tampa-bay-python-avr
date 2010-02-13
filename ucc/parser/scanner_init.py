# scanner_init.py

import sys
import os.path
import re
from ucc.parser.ply import lex

#sys.stderr.write("scanner_init: lex.__file__ is %r\n" % (lex.__file__,))
#sys.stderr.write("scanner_init: sys.path[0] is %r\n" % (sys.path[0],))
#sys.stderr.write("scanner_init: sys.path[1] is %r\n" % (sys.path[1],))

Lexer = None
Scanner_module = None

def get_syntax_position_info(p):
    return get_lineno_column(p, 1) + get_lineno_column(p, len(p) - 1)

def get_lineno_column(p, index):
    return p.lineno(index), get_col_line(p.lexpos(index))[0]

def get_col_line(lexpos, lexdata = None):
    r'''Returns the line and column number for the given lexdata and lexpos.

    The lexdata is the entire input file and lexpos is the offset within
    lexdata.

    >>> lexdata = "hi there\ndid you see this?\r\n   I hope so!"
    >>> get_col_line(lexdata.index('h'), lexdata)
    (1, 'hi there')
    >>> get_col_line(lexdata.index('t'), lexdata)
    (4, 'hi there')
    >>> get_col_line(lexdata.index('d'), lexdata)
    (1, 'did you see this?')
    >>> get_col_line(lexdata.index('y'), lexdata)
    (5, 'did you see this?')
    >>> get_col_line(lexdata.index('?'), lexdata)
    (17, 'did you see this?')
    >>> get_col_line(lexdata.index('p'), lexdata)
    (8, '   I hope so!')
    >>> get_col_line(lexdata.index('!'), lexdata)
    (13, '   I hope so!')
    '''
    if lexdata is None: lexdata = Lexer.lexdata
    start = lexdata.rfind('\n', 0, lexpos) + 1
    if start < 0: start = 0
    column = lexpos - start + 1
    end = lexdata.find('\n', lexpos)
    if end < 0: end = len(lexdata)
    if lexdata[end - 1] == '\r': end -= 1
    return column, lexdata[start:end]

def syntaxerror_params(t = None, lineno = None, lexpos = None):
    if lexpos is None:
        if t is None: lexpos = Lexer.lexpos
        else: lexpos = t.lexpos
    if lineno is None: lineno = Lexer.lineno
    return (Lexer.filename, lineno) + get_col_line(lexpos)

def syntaxerror(msg, t = None, lineno = None, lexpos = None):
    r'''Prints out syntax error info to stderr, then raises SyntaxError.'''
    filename, lineno, column, line = syntaxerror_params(t, lineno, lexpos)
    sys.stderr.write("SyntaxError in file %r at line %d:\n" % 
                       (filename, lineno))
    sys.stderr.write("    %s\n" % line)
    sys.stderr.write("    %s^\n" % (' ' * (column - 1)))
    sys.stderr.write(msg + '\n')
    raise SyntaxError

def init(scanner_module, debug_param, check_tables = False, extra_arg = None):
    global Lexer, Scanner_module
    if extra_arg is None:
        scanner_module.init(debug_param)
    else:
        scanner_module.init(debug_param, extra_arg)
    if Lexer is None or Scanner_module != scanner_module:
        if debug_param:
            Lexer = lex.lex(module=scanner_module, reflags=re.VERBOSE, debug=1)
        else:
            tables_name = scanner_module.__name__ + "_tables"
            #module_name = scanner_module.__name__.split('.')[-1]
            #tables_name = "%s_tables" % module_name
            if check_tables:
                scanner_mtime = os.path.getmtime(scanner_module.__file__)
                tables_path = \
                    os.path.join(os.path.dirname(scanner_module.__file__),
                                 tables_name.split('.')[-1] + '.py')
                #sys.stderr.write("tables_path: %r\n" % tables_path)
                try:
                    ok = os.path.getmtime(tables_path) >= scanner_mtime
                    #sys.stderr.write("********tables_path exists: ok is %r\n"
                    #                   % ok)
                except OSError:
                    #sys.stderr.write("********tables_path does not exist\n")
                    ok = False
                if not ok:
                    #sys.stderr.write("********removing scanner_tables\n")
                    #print "regenerating scanner_tables"
                    try: os.remove(tables_path)
                    except OSError: pass
                    try: os.remove(tables_path + 'c')
                    except OSError: pass
                    try: os.remove(tables_path + 'o')
                    except OSError: pass
            Lexer = lex.lex(module=scanner_module, optimize=1,
                            lextab=tables_name,
                            reflags=re.VERBOSE,
                            outputdir=os.path.dirname(scanner_module.__file__))
        Scanner_module = scanner_module

def tokenize(scanner_module, s, extra_arg = None):
    r'''A function to help with testing your scanner.

        #>>> from ucc.parser import scanner
        #>>> tokenize(scanner, '22\n')
        #LexToken(INTEGER_TOK,22,1,0)
        #LexToken(NEWLINE_TOK,'\n',1,2)
        #>>> tokenize(scanner, '# comment1\n\n    \n    # comment2\n44\n')
        #LexToken(NEWLINE_TOK,'\n',4,31)
        #LexToken(INTEGER_TOK,44,5,32)
        #LexToken(NEWLINE_TOK,'\n',5,34)
    '''
    init(scanner_module, 0, True, extra_arg)
    Lexer.filename = 'tokenize'
    Lexer.lineno = 1
    if s[-1] not in ' \n': s += ' '
    Lexer.input(s)
    Lexer.begin('INITIAL')
    while True:
        t = Lexer.token()
        if not t: break
        print t
