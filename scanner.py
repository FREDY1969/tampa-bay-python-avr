# scanner.py

# See http://www.dabeaz.com/ply/ply.html for syntax of grammer definitions.

from __future__ import with_statement, division

from ply import lex
import word
import domain
import number

debug = 0

states = (
    ('colonindent', 'exclusive'),
    ('indent', 'exclusive'),
    ('string', 'exclusive'),
)

tokens = (
    'CHAR_TOK',
    'DEINDENT_TOK',
    'INDENT_TOK',
    'LP_TOK',
    'NAME_TOK',
    'NEWLINE_TOK',
    'NUMBER_TOK',
    'START_PARAMS_TOK',
    'START_SERIES_TOK',
    'STRING_TOK',
    'WORD_TOK',
)

literals = ')]'

t_ignore = ' '

t_ignore_comment = r'(?<![^ \r\n])\#.*'

def t_continuation(t):
    r'''(?<!\\)                 # can't come after another backslash!
        \\                      # backslash
        (?:\ \ *(?:\#.*)?)?     # optional spaces, optional comment
        (?:\r)?\n               # newline
    '''
    t.lexer.lineno += 1

def t_START_SERIES_TOK(t):
    r''':                       # :
        (?:\ \ *(?:\#.*)?)?     # optional spaces, optional comment
        (?:\r)?\n               # newline
    '''
    t.lexer.begin('colonindent')
    t.lexer.skip(-1)
    return t

last_colonindent = 0

t_colonindent_ignore = ''

def t_colonindent_sp(t):
    r'\n\ *'
    indent = len(t.value) - 1
    if indent % 4:
        raise SyntaxError("improper indent level, must be multiple of 4",
                          syntaxerror_params())
    if indent > last_colonindent:
        if indent != last_colonindent + 4:
            raise SyntaxError("multiple indent", syntaxerror_params())
        last_colonindent = indent
        t.lexer.begin('INITIAL')
        return 'INDENT_TOK'
    if indent < last_colonindent:
        if indent < last_colonindent - 4:
            t.lexer.skip(-len(t.value))         # play it again, Sam...
        else:
            t.lexer.begin('INITIAL')
        last_colonindent -= 4
        return 'DEINDENT_TOK'
    t.lexer.begin('INITIAL')

def t_NEWLINE_TOK(t):
    r'''(?:\r)?\n                       # newline
        (?:\ *(?:\#.*)?(?:\r)?\n)*      # blank lines
    '''
    t.lexer.lineno += t.value.count('\n')
    t.lexer.begin('indent')
    t.lexer.skip(-1)
    return t

indent_levels = []
last_indent = 0

t_indent_ignore = ''

def t_indent_sp(t):
    r'\n\ *'
    global indent_levels, last_indent
    indent = len(t.value) - 1
    try:
        level = indent_levels.index(indent)
    except ValueError:
        if indent == 0 and not indent_levels:
            indent_levels.append(0)
            last_indent = 0
            t.lexer.begin('INITIAL')
            return
        raise SyntaxError("invalid indent level, "
                            "doesn't match anything on previous line",
                          syntaxerror_params())
    if level > last_indent:
        if level == last_indent + 1:
            t.lexer.begin('INITIAL')
        last_indent += 1
        return 'INDENT_TOK'
    if indent < last_indent:
        if level == last_indent - 1:
            t.lexer.begin('INITIAL')
        last_indent -= 1
        return 'DEINDENT_TOK'
    t.lexer.begin('INITIAL')

def t_CHAR_TOK(t):
    r"'[^\\]'"
    t.value = ord(t.value[1])
    return t

escapes = {
    'a': '\a',
    'b': '\b',
    'f': '\f',
    'n': '\n',
    'r': '\r',
    't': '\t',
    'v': '\v',
}

def t_escaped_char_tok(t):
    r"'\\[^x]'"
    t.value = ord(escapes.get(t.value[2], t.value[2]))
    t.type = 'CHAR_TOK'
    return t

def t_hex_char_tok(t):
    r"'\\x[0-9a-fA-F]{2}'"
    t.value = int(t.value[3:], 16)
    t.type = 'CHAR_TOK'
    return t

def t_start_string(t):
    r'"'
    global string_value
    t.lexer.begin('string')
    string_value = ""

def t_string_end(t):
    r'"'
    t.value = string_value
    t.lexer.begin('INITIAL')
    t.type = 'STRING_TOK'
    return t

t_string_ignore = ''

def t_string_char(t):
    r'[^\\"]'
    string_value += t.value[1]

def t_string_escaped_char(t):
    r'\\[^x]'
    string_value += escapes.get(t.value[2], t.value[2])

def t_string_hex_char(t):
    r'\\x[0-9a-fA-F]{2}'
    string_value += int(t.value[3:], 16)

def t_LP_TOK(t):
    r'''(?<![^[( ])     # preceeded by [, (, or space, or at start of line
        \(
    '''
    return t

def t_START_PARAMS_TOK(t):
    r'\('
    return t

def t_LB_TOK(t):
    r'''(?<![^[( ])     # preceeded by [, (, or space, or at start of line
        \[
    '''
    return t

def t_START_SUBSCRIPT_TOK(t):
    r'\['
    return t

def t_NUMBER_TOK(t):
    r'''(?<![^[( ])     # preceeded by [, (, or space, or at start of line
        [0-9]+
        (?:\.[0-9]+)?   # optional decimal point
        /[0-9]*         # denominator
        (?=[]) \r\n])   # followed by ], ), space or newline
    '''
    t.value = number.any_precision.from_str(t.value, 10).to_domain()
    return t

def t_HEX_NUMBER_TOK(t):
    r'''(?<![^[( ])         # preceeded by [, (, or space, or at start of line
        0[xX][0-9a-fA-F]+
        (?:\.[0-9a-fA-F]+)? # optional decimal part
        /[0-9a-fA-F]*       # denominator
        (?=[]) \r\n])       # followed by ], ), space or newline
    '''
    t.value = number.any_precision.from_str(t.value, 16).to_domain()
    t.type = 'NUMBER_TOK'
    return t

def t_APPROX_NUMBER_TOK(t):
    r'''(?<![^[( \r\n])  # preceeded by [, (, or space, or at start of line
        [0-9]+
        (?: \.[0-9]+ (?: ~[0-9])?
          | ~[0-9]+)?
        (?=[]) \r\n])    # followed by ], ), space or newline
    '''
    t.value = number.fixed_precision.from_str(t.value, 10).to_domain()
    t.type = 'NUMBER_TOK'
    return t

def t_HEX_APPROX_NUMBER_TOK(t):
    r'''(?<![^[( ])      # preceeded by [, (, or space, or at start of line
        0[xX][0-9a-fA-F]+
        (?: \.[0-9a-fA-F]+ (?: ~[0-9a-fA-F])?
          | ~[0-9a-fA-F]+)?
        (?=[]) \r\n])    # followed by ], ), space or newline
    '''
    t.value = number.fixed_precision.from_str(t.value, 16).to_domain()
    t.type = 'NUMBER_TOK'
    return t

def t_NAME_TOK(t):
    r'''(?<![^[( -])      # preceeded by [, (, -, or space, or at start of line
        [^][() "'\r\n#]+
        [^][() "'\r\n]*
        (?=[][() \r\n])   # followed by [, ], (, ), space or newline
    '''
    if t.value in dictionary:
        t.value = self.dictionary[t.value]
        t.type = 'WORD_TOK'
    return t

def t_negate(t):
    r'''(?<![^[( -])       # preceeded by [, (, -, or space, or at start of line
        -
        (?=[^][() "'\r\n]) # followed by name or number
    '''
    if 'negate' in dictionary:
        t.value = dictionary['negate']
        t.type = 'WORD_TOK'
    else:
        t.type = 'NAME_TOK'
    return t

def t_minus(t):
    r'''(?<![^ ])       # preceeded by space or at start of line
        -
        (?=[ \r\n])     # followed by space or newline
    '''
    if '-' in dictionary:
        t.value = dictionary['-']
        t.type = 'WORD_TOK'
    else:
        t.type = 'NAME_TOK'
    return t

def t_ANY_error(t):
    raise SyntaxError("Scanner error: possible illegal character %r" %
                        t.value[0],
                      syntaxerror_params())

def syntaxerror_params():
    pos = lexer.lexpos
    start = pos
    lineno = lexer.lineno
    while start > 0 and (start >= len(lexer.lexdata) or
                         lexer.lexdata[start] in '\r\n'):
        start -= 1
    end = start
    if debug: print "pos", pos, "lineno", lineno, "start", start
    start = max(lexer.lexdata.rfind('\r', 0, start),
                lexer.lexdata.rfind('\n', 0, start)) + 1
    column = pos - start + 1
    end1 = lexer.lexdata.find('\r', end)
    end2 = lexer.lexdata.find('\n', end)
    if end1 < 0: end = end2
    elif end2 < 0: end = end1
    else: end = min(end1, end2)
    if debug: print "start", start, "column", column, "end", end
    return (lexer.filename, lineno, column, lexer.lexdata[start:end])

lexer = None

def init(this_module, word_dict, debug_param, check_tables = False):
    global last_colonindent, indent_levels, last_indent, debug, lexer
    global dictionary
    last_colonindent = 0
    indent_levels = []
    last_indent = 0
    debug = debug_param
    dictionary = word_dict
    if lexer is None:
        if debug_param:
            lexer = lex.lex(module=this_module, debug=1)
        else:
            if check_tables:
                scanner_mtime = os.path.getmtime(this_module.__file__)
                tables_name = \
                    os.path.join(os.path.dirname(this_module.__file__),
                                 'scanner_tables.py')
                try:
                    ok = os.path.getmtime(tables_name) >= scanner_mtime
                except OSError:
                    ok = False
                if not ok:
                    #print "regenerating scanner_tables"
                    try: os.remove(tables_name)
                    except OSError: pass
                    try: os.remove(tables_name + 'c')
                    except OSError: pass
                    try: os.remove(tables_name + 'o')
                    except OSError: pass
            lexer = lex.lex(module=this_module, optimize=1,
                            lextab='scanner_tables',
                            outputdir=os.path.dirname(this_module.__file__))

def tokenize(this_module, word_dict, s):
    r'''
        >>> import scanner
        >>> scanner.tokenize(scanner, {}, '22\n')
        LexToken(NUMBER_TOK,<constant 22: <approx 22-22 .1 ~1>>,1,0)
        LexToken(NEWLINE_TOK,'\n',1,2)
        >>> scanner.tokenize(scanner, {},
        ...                  '# comment1\n\n    \n    # comment2\n44\n')
        LexToken(NEWLINE_TOK,'\n\n    \n    # comment2\n',1,10)
        LexToken(NUMBER_TOK,<constant 44: <approx 44-44 .1 ~1>>,5,32)
        LexToken(NEWLINE_TOK,'\n',5,34)
    '''
    init(this_module, word_dict, 1, True)
    lexer.filename = 'tokenize'
    lexer.lineno = 1
    lexer.input(s)
    lexer.begin('INITIAL')
    while True:
        t = lex.token()
        if not t: break
        print t
