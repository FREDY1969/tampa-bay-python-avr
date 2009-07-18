# parser_init.py

import os, os.path
from ply import yacc

Parser = None

def init(parser_module, check_tables = False, debug = 0):
    global Parser
    if Parser is None:
        outputdir = os.path.dirname(parser_module.__file__)
        module_name = parser_module.__name__.split('.')[-1]
        if debug:
            Parser = yacc.yacc(module=parser_module, write_tables=0,
                               debug=debug,
                               debugfile=module_name + '.out',
                               outputdir=outputdir)
        else:
            if check_tables:
                parser_mtime = os.path.getmtime(parser_module.__file__)
                tables_name = os.path.join(outputdir,
                                           module_name + '_tables.py')
                try:
                    ok = os.path.getmtime(tables_name) >= parser_mtime
                except OSError:
                    ok = False
                if not ok:
                    #print "regenerating parser_tables"
                    try: os.remove(tables_name)
                    except OSError: pass
                    try: os.remove(tables_name + 'c')
                    except OSError: pass
                    try: os.remove(tables_name + 'o')
                    except OSError: pass
            Parser = yacc.yacc(module=parser_module, debug=0,
                               optimize=1, write_tables=1,
                               tabmodule=module_name + '_tables',
                               outputdir=outputdir)

# Use the debug = 0 for normal use, and debug = 1 for testing changes in the
# grammer (debug = 0 does not report grammer errors!).
def parse(parser_module, scanner_module, filename, check_tables = False,
#          debug = 0):
          debug = 1):
    init(parser_module, check_tables, debug)
    with open(filename) as f:
        scanner_init.init(scanner_module, debug, check_tables)
        scanner_init.Lexer.lineno = 1
        scanner_init.Lexer.filename = filename
        #Parser.restart()
        text = f.read()
        if text[-1] not in ' \n': text += ' '
        return Parser.parse(text, lexer=scanner_init.Lexer, tracking=True,
                            debug=debug)

def run(parser_module, scanner_module, filename):
    r""" Used for testing.

        #>>> import os, os.path
        #>>> from ucc.parser import parser, scanner
        #>>> run(parser, scanner,
        #...     'TEST/krbparse_test.krb'
        #...     if os.path.split(os.getcwd())[1] == 'krb_compiler'
        #...     else 'krb_compiler/TEST/krbparse_test.krb')

    """
    import pprint
    pprint.pprint(parse(parser_module, scanner_module, filename, True))

