# parser_init.py

import os, os.path
from ply import yacc
from ucc.parser import scanner_init

Parser = None

def init(parser_module, check_tables = False, debug = 0):
    global Parser
    parser_module.init()
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
                               tabmodule=parser_module.__name__ + '_tables',
                               outputdir=outputdir)

# Use the debug = 0 for normal use, and debug = 1 for testing changes in the
# grammer (debug = 0 does not report grammer errors!).
def parse(parser_module, scanner_module, filename, check_tables = False,
          debug = 0, text = None, extra_arg = None):
#          debug = 1, text = None, extra_arg = None):
    init(parser_module, check_tables, debug)
    scanner_init.init(scanner_module, debug, check_tables, extra_arg)
    scanner_init.Lexer.lineno = 1
    scanner_init.Lexer.filename = filename
    if text is None:
        with open(filename) as f:
            #Parser.restart()
            text = f.read()
    if text[-1] not in ' \n': text += ' '
    return Parser.parse(text, lexer=scanner_init.Lexer, tracking=True,
                        debug=debug)

def test(parser_module, scanner_module, text):
    r''' Used for testing.

        #>>> import os, os.path
        #>>> from ucc.parser import parser, scanner
        #>>> test(parser, scanner,
        #...     r"""
        #...     blah blah blah
        #...     """)

    '''
    import pprint
    import StringIO
    pprint.pprint(parse(parser_module, scanner_module, 'test', True, 0, text))

