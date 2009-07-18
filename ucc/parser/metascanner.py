# metascanner.py

# See http://www.dabeaz.com/ply/ply.html for syntax of grammer definitions.

from __future__ import with_statement, division
from ucc.parser import scanner_init

debug = 0

states = (
    ('python', 'exclusive'),
)

tokens = (
    'AS_TOK',
    'NEWLINE_TOK',
    'NONTERMINAL',
    'TUPLE_NONTERMINAL',
    'ELLIPSIS',
    'TOKEN_IGNORE',
    'CHAR_TOKEN',
    'TOKEN',
    'PYTHON_CODE',
)

literals = '(){}:|?+*,'

t_ignore = ' '

t_ignore_comment = r'\#[^\t\r\n]*'

def t_NEWLINE_TOK(t):
    r'''(?:\r)? \n                          # newline
        (?: \ *
            (?: \#[^\t\r\n]* )?
            (?:\r)? \n
          )*                                # any number of blank lines
        [^#]                                # first character of next line
    '''
    t.lexer.lineno += t.value.count('\n')
    test_char = t.value[-1]
    t.lexer.skip(-1)                        # push back the final '\n'
    if test_char != ' ':
        return t

def t_NEWLINE_TOK2(t):
    r'''(?:\r)? \n                          # newline
        (?: \ *
            (?: \#[^\t\r\n]* )?
            (?:\r)? \n
          )*                                # any number of blank lines
    '''
    # assume we're at EOF here...
    print "t_NEWLINE_TOK2"
    pass

def t_AS_TOK(t):
    r'''as'''
    return t

t_NONTERMINAL = r'[a-z_][a-z_0-9]*'

def t_TUPLE_NONTERMINAL(t):
    r'''\[[a-z_][a-z_0-9]*\]
    '''
    t.value = t.value[1:-1]
    return t

t_ELLIPSIS = r'\.\.\.'

def t_TOKEN_IGNORE(t):
    r'[A-Z_][A-Z_0-9]*_TOK'
    # Defined as function to override t_TOKEN.
    return t

t_TOKEN = r'[A-Z_][A-Z_0-9]*'

t_CHAR_TOKEN = r"'[^\\\t\r\n ]'"

def t_start_python_code(t):
    r'='
    global Python_code, Python_current_quote
    t.lexer.begin('python')
    Python_code = ''
    Python_current_quote = None

t_python_ignore = ''

def t_python_escape(t):
    r'''\\.'''
    global Python_code
    Python_code += t.value

def t_python_quote(t):
    r'''['"]'''
    global Python_code, Python_current_quote
    if Python_current_quote is None:
        Python_current_quote = t.value
    elif Python_current_quote == t.value:
        Python_current_quote = None
    Python_code += t.value

def t_PYTHON_CODE(t):
    r'''[,)]'''
    global Python_code, Python_current_quote
    if Python_current_quote is None:
        t.lexer.begin('INITIAL')
        t.lexer.skip(-1)
        t.value = Python_code
        return t
    Python_code += t.value

def t_ANY_error(t):
    raise SyntaxError("Scanner error: possible illegal character %r" %
                        t.value[0],
                      scanner_init.syntaxerror_params())

def init(debug_param):
    r'''
        >>> from ucc.parser import metascanner as ms, scanner_init as si
        >>> si.tokenize(ms,
        ...                       "# comment1\n"
        ...                       "\n"
        ...                       "    \n"
        ...                       "hi: MOM 'x'\n"
        ...                       " | MORE_TOK")
        LexToken(NEWLINE_TOK,'\n\n    \nh',1,10)
        LexToken(NONTERMINAL,'hi',4,17)
        LexToken(:,':',4,19)
        LexToken(TOKEN,'MOM',4,21)
        LexToken(CHAR_TOKEN,"'x'",4,25)
        LexToken(|,'|',5,30)
        LexToken(TOKEN_IGNORE,'MORE_TOK',5,32)
    '''
    debug = debug_param

