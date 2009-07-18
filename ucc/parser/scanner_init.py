# scanner_init.py

import os.path
from ply import lex

Lexer = None

def get_col_line(lexdata, lexpos):
    r'''Returns the line and column number for the given lexdata and lexpos.

    The lexdata is the entire input file and lexpos is the offset within
    lexdata.

    >>> lexdata = "hi there\ndid you see this?\r\n   I hope so!"
    >>> get_col_line(lexdata, lexdata.index('h'))
    (1, 'hi there')
    >>> get_col_line(lexdata, lexdata.index('t'))
    (4, 'hi there')
    >>> get_col_line(lexdata, lexdata.index('d'))
    (1, 'did you see this?')
    >>> get_col_line(lexdata, lexdata.index('y'))
    (5, 'did you see this?')
    >>> get_col_line(lexdata, lexdata.index('?'))
    (17, 'did you see this?')
    >>> get_col_line(lexdata, lexdata.index('p'))
    (8, '   I hope so!')
    >>> get_col_line(lexdata, lexdata.index('!'))
    (13, '   I hope so!')
    '''
    start = lexdata.rfind('\n', 0, lexpos) + 1
    if start < 0: start = 0
    column = lexpos - start + 1
    end = lexdata.find('\n', lexpos)
    if end < 0: end = len(lexdata)
    if lexdata[end - 1] == '\r': end -= 1
    return column, lexdata[start:end]

def syntaxerror_params(t = None):
    return (Lexer.filename, Lexer.lineno) + \
           get_col_line(Lexer.lexdata, (t.lexpos if t else Lexer.lexpos))

def init(scanner_module, debug_param, check_tables = False, extra_arg = None):
    global Lexer
    if extra_arg is None:
        scanner_module.init(debug_param)
    else:
        scanner_module.init(debug_param, extra_arg)
    if Lexer is None:
        if debug_param:
            Lexer = lex.lex(module=scanner_module, debug=1)
        else:
            module_name = scanner_module.__name__.split('.')[-1]
            tables_name = "%s_tables" % module_name
            if check_tables:
                scanner_mtime = os.path.getmtime(scanner_module.__file__)
                tables_path = \
                    os.path.join(os.path.dirname(scanner_module.__file__),
                                 tables_name + '.py')
                try:
                    ok = os.path.getmtime(tables_path) >= scanner_mtime
                except OSError:
                    ok = False
                if not ok:
                    #print "regenerating scanner_tables"
                    try: os.remove(tables_path)
                    except OSError: pass
                    try: os.remove(tables_path + 'c')
                    except OSError: pass
                    try: os.remove(tables_path + 'o')
                    except OSError: pass
            Lexer = lex.lex(module=scanner_module, optimize=1,
                            lextab=tables_name,
                            outputdir=os.path.dirname(scanner_module.__file__))

def tokenize(scanner_module, s, extra_arg = None):
    r'''A function to help with testing your scanner.

        #>>> import scanner
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
        t = lex.token()
        if not t: break
        print t
