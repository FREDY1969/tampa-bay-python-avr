# scanner.py

# See http://www.dabeaz.com/ply/ply.html for syntax of grammer definitions.



from ucc.parser import scanner_init, number
from ucc.database import ast, symbol_table

debug = 0

states = (
    ('colonindent', 'exclusive'),
    ('indent', 'exclusive'),
    ('string', 'exclusive'),
)

tokens = (
    'AND',
    'APPROX_NUMBER',
    'ARG_LEFT_WORD',
    'ARG_RIGHT_WORD',
    'BIT_AND',
    'BIT_NOT',
    'BIT_OR',
    'BIT_XOR',
    'CHAR',
    'DEINDENT_TOK',
    'EQ',
    'GE',
    'INDENT_TOK',
    'INTEGER',
    'LB_TOK',
    'LE',
    'LP_TOK',
    'NAME',
    'NE',
    'NEGATE',
    'NEWLINE_TOK',
    'NOT',
    'OR',
    'RATIO',
    'START_SERIES_TOK',
    'STRING',
)

literals = '()[]:'

t_ignore = ' '

t_ignore_comment = r'\#[^\t\r\n]*'

def t_START_SERIES_TOK(t):
    r''':                               # :
        (?:\ \ *(?:\#[^\t\r\n]*)?)?     # optional spaces, optional comment
        (?:\r)?\n                       # newline
    '''
    t.lexer.lineno += 1
    t.lexer.begin('colonindent')
    t.lexer.skip(-1)                    # push back the final '\n'
    return t

#Last_colonindent = 0

t_colonindent_ignore = ''

def t_colonindent_blank_line(t):
    r'\n (?: \ * (?: \# [^\t\r\n]* )? (?:\r)? \n )+'
    t.lexer.lineno += t.value.count('\n') - 1

def t_colonindent_INDENT_TOK(t):
    r'\n\ *'
    global Last_colonindent
    indent = len(t.value) - 1
    if indent != Last_colonindent + 4:
        raise SyntaxError("improper indent level after :",
                          scanner_init.syntaxerror_params())
    Last_colonindent = indent
    t.lexer.begin('INITIAL')
    return t

def t_NEWLINE_TOK(t):
    r'(?:\r)?\n'                       # newline
    global Sent_newline
    t.lexer.begin('indent')
    t.lexer.skip(-1)                   # push back the final '\n'
    Sent_newline = False

t_indent_ignore = ''

def t_indent_blank_line(t):
    r'\n(?: \ * (?: \# [^\t\r\n]* )? (?:\r)? \n )+'
    t.lexer.lineno += t.value.count('\n') - 1
    t.lexer.skip(-1)                   # push back the final '\n'

def t_indent_sp(t):
    r'\n\ *'
    global Last_colonindent, Sent_newline
    indent = len(t.value) - 1
    if indent == Last_colonindent:
        t.lexer.lineno += 1
        t.lexer.begin('INITIAL')
        t.type = 'NEWLINE_TOK'
        return t
    if indent > Last_colonindent:
        t.lexer.lineno += 1
        t.lexer.begin('INITIAL')
        return
    if indent % 4:
        raise SyntaxError("invalid indent level, must be multiple of 4 spaces",
                          scanner_init.syntaxerror_params())
    if not Sent_newline:
        t.lexer.lineno += 1
        t.lexer.skip(-len(t.value))     # come back here after NEWLINE_TOK
        t.type = 'NEWLINE_TOK'
        Sent_newline = True
        return t
    t.type = 'DEINDENT_TOK'
    Last_colonindent -= 4
    if indent == Last_colonindent:
        t.lexer.begin('INITIAL')
    else:
        t.lexer.skip(-len(t.value))     # come back here after DEINDENT_TOK
    return t

def t_CHAR(t):
    r"'[^\\\t\r\n]'"
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
    r"'\\[^xX\t\r\n]'"
    t.value = ord(escapes.get(t.value[2].lower(), t.value[2]))
    t.type = 'CHAR'
    return t

def t_hex_char_tok(t):
    r"'\\[xX][0-9a-fA-F]{2}'"
    t.value = int(t.value[3:-1], 16)
    t.type = 'CHAR'
    return t

def t_start_string(t):
    r'"'
    global String_value, Start
    t.lexer.begin('string')
    Start = t.lexpos
    String_value = ""

t_string_ignore = ''

def t_string_char(t):
    r'[^\\"\t\r\n]'
    global String_value
    String_value += t.value[0]

def t_string_escaped_char(t):
    r'\\[^xX\t\r\n]'
    global String_value
    String_value += escapes.get(t.value[1].lower(), t.value[1])

def t_string_hex_char(t):
    r'\\[xX][0-9a-fA-F]{2}'
    global String_value
    String_value += chr(int(t.value[2:], 16))

def t_string_STRING(t):
    r'"'
    t.value = String_value
    t.lexpos = Start
    t.lexer.begin('INITIAL')
    return t

def t_LP_TOK(t):
    r'''(?<![^[( ])     # preceded by [, (, or space, or at start of line
        \(
    '''
    return t

def t_LB_TOK(t):
    r'''(?<![^[( ])     # preceded by [, (, or space, or at start of line
        \[
    '''
    return t

def t_RATIO(t):
    r'''[0-9]+/[0-9]+   # ratio
        (?=[[(:]?[]) \r\n])   # followed by ], ), space or newline
    '''
    slash = t.value.index('/')
    t.value = (int(t.value[:slash]), int(t.value[slash+1:]))
    return t

def t_ratio_2(t):
    r'''[0-9]+
        \.[0-9]+              # decimal point
        /[0-9]+               # denominator
        (?=[[(:]?[]) \r\n])   # followed by ], ), space or newline
    '''
    dot = t.value.index('.')
    slash = t.value.index('/')
    denominator = int(t.value[slash+1:])
    t.value = (int(t.value[:dot]) * denominator + int(t.value[dot+1:slash]),
               denominator)
    t.type = 'RATIO'
    return t

def t_ratio_3(t):
    r'''[0-9]+
        \.[0-9]+              # decimal point
        /                     # implied denominator
        (?=[[(:]?[]) \r\n])   # followed by ], ), space or newline
    '''
    dot = t.value.index('.')
    denominator = 10**(len(t.value) - dot - 2)
    t.value = (int(t.value[:dot]) * denominator + int(t.value[dot + 1:-1]),
               denominator)
    t.type = 'RATIO'
    return t

def t_ratio_4(t):
    r'''\.[0-9]+              # decimal point
        /                     # implied denominator
        (?=[[(:]?[]) \r\n])   # followed by ], ), space or newline
    '''
    denominator = 10**(len(t.value) - 2)
    t.value = (int(t.value[1:-1]), denominator)
    t.type = 'RATIO'
    return t

def t_hex_RATIO(t):
    r'''0[xX][0-9a-fA-F]+/[0-9a-fA-F]+ # ratio
        (?=[[(:]?[]) \r\n])            # followed by ], ), space or newline
    '''
    slash = t.value.index('/')
    t.value = (int(t.value[:slash], 16), int(t.value[slash+1:], 16))
    t.type = 'RATIO'
    return t

def t_hex_ratio_2(t):
    r'''0[xX][0-9a-fA-F]+
        \.[0-9a-fA-F]+        # decimal point
        /[0-9a-fA-F]+         # denominator
        (?=[[(:]?[]) \r\n])   # followed by ], ), space or newline
    '''
    dot = t.value.index('.')
    slash = t.value.index('/')
    denominator = int(t.value[slash + 1:], 16)
    t.value = (int(t.value[:dot], 16) * denominator +
                 int(t.value[dot + 1:slash], 16),
               denominator)
    t.type = 'RATIO'
    return t

def t_hex_ratio_3(t):
    r'''0[xX][0-9a-fA-F]+
        \.[0-9a-fA-F]+        # decimal point
        /                     # implied denominator
        (?=[[(:]?[]) \r\n])   # followed by ], ), space or newline
    '''
    dot = t.value.index('.')
    denominator = 16**(len(t.value) - dot - 2)
    t.value = (int(t.value[:dot], 16) * denominator +
                 int(t.value[dot + 1:-1], 16),
               denominator)
    t.type = 'RATIO'
    return t

def t_hex_ratio_4(t):
    r'''0[xX]
        \.[0-9a-fA-F]+        # decimal point
        /                     # implied denominator
        (?=[[(:]?[]) \r\n])   # followed by ], ), space or newline
    '''
    denominator = 16**(len(t.value) - 4)
    t.value = (int(t.value[3:-1], 16), denominator)
    t.type = 'RATIO'
    return t

def t_APPROX_NUMBER(t):
    # All decimal forms with a '.':
    r'''(?: [0-9]+ \.[0-9]* | \.[0-9]+ )
        (?: ~[0-9] )?
        (?: [eE] [+-]?[0-9]+ )?
        (?=[[(:]?[]) \r\n])    # followed by ], ), space or newline
    '''
    t.value = number.approx(t.value).int_exp()
    return t

def t_approx_2(t):
    # All decimal forms without a '.':
    r'''[0-9]+ (?: (?: ~[0-9] )? [eE] [+-]?[0-9]+ | ~[0-9] )
        (?=[[(:]?[]) \r\n])    # followed by ], ), space or newline
    '''
    t.value = number.approx(t.value).int_exp()
    t.type = 'APPROX_NUMBER'
    return t

def t_hex_APPROX_NUMBER(t):
    # All hex forms with a '.':
    r'''0[xX] (?: [0-9a-fA-F]+ \.[0-9a-fA-F]* | \.[0-9a-fA-F]+ )
              (?: ~[0-9a-fA-F] )?
              (?: [xX] [+-]?[0-9]+ )?
        (?=[[(:]?[]) \r\n])    # followed by ], ), space or newline
    '''
    t.value = number.approx(t.value).int_exp()
    t.type = 'APPROX_NUMBER'
    return t

def t_hex_approx_2(t):
    # All hex forms without a '.':
    r'''0[xX] [0-9a-fA-F]+
        (?: (?: ~[0-9a-fA-F] )? [xX] [+-]?[0-9]+
          | ~[0-9a-fA-F] )
        (?=[[(:]?[]) \r\n])    # followed by ], ), space or newline
    '''
    t.value = number.approx(t.value).int_exp()
    t.type = 'APPROX_NUMBER'
    return t

def t_INTEGER(t):
    r'''[0-9]+
        (?=[[(:]?[]) \r\n])   # followed by ], ), space or newline
    '''
    t.value = int(t.value)
    return t

def t_hex_INTEGER(t):
    r'''0[xX][0-9]+
        (?=[[(:]?[]) \r\n])   # followed by ], ), space or newline
    '''
    t.value = int(t.value, 16)
    t.type = 'INTEGER'
    return t

Names = {
    '<': '<',
    '>': '>',
    '-': '-',
    '/': '/',
    '*': '*',
    '%': '%',
    '+': '+',
    'and': 'AND',
    'bit-and': 'BIT_AND',
    'bit-not': 'BIT_NOT',
    'bit-or': 'BIT_OR',
    'bit-xor': 'BIT_XOR',
    '=': 'EQ',
    '>=': 'GE',
    '<=': 'LE',
    '!=': 'NE',
    'not': 'NOT',
    'or': 'OR',
}

def t_NAME_n(t):
    r'''[^[( \r\n."'#-]     # first character
        [^[( \r\n.]*        # middle characters
        [^])[( \r\n.:]      # last character
    '''
    if t.value in Names:
        t.type = Names[t.value]
        set_name_value(t)
    elif t.value in Token_dict:
        t.type = Token_dict[t.value]
        if not t.type.endswith('_TOK'): 
            set_name_value(t)
    elif t.value[0] == '>':
        t.type = 'ARG_LEFT_WORD'
        set_name_value(t)
    elif t.value[-1] == '<':
        t.type = 'ARG_RIGHT_WORD'
        set_name_value(t)
    else:
        t.type = 'NAME'
        set_name_value(t)
    return t

def t_NAME(t): # single character NAME
    r'''[^])[( \r\n.:"'#-]
        (?=[])[( \r\n.:])    # followed by [, ], (, ), space, newline, . or :
    '''
    if t.value in Names:
        t.type = Names[t.value]
        set_name_value(t)
    elif t.value in Token_dict:
        t.type = Token_dict[t.value]
        if not t.type.endswith('_TOK'): 
            set_name_value(t)
    else:
        set_name_value(t)
    return t

def t_NEGATE(t):
    r'''-
        (?=[^]) \r\n])  # followed by name, number, string, -, ( or [
    '''
    set_name_value(t, 'negate')
    return t

def t_minus(t):
    r'''-
        (?=[ \r\n])     # followed by space or newline
    '''
    t.type = '-'
    set_name_value(t)
    return t

def t_ANY_error(t):
    raise SyntaxError("Scanner error: possible illegal character %r" %
                        t.value[0],
                      scanner_init.syntaxerror_params())


def init(debug_param, extra_arg = (None, {})):
    r'''
        >>> from ucc.parser import scanner
        >>> from ucc.parser import scanner_init
        >>> scanner_init.tokenize(scanner, '22\n')
        LexToken(INTEGER,22,1,0)
        LexToken(NEWLINE_TOK,'\n',1,2)
        >>> scanner_init.tokenize(scanner,
        ...                       '# comment1\n\n    \n    # comment2\n44\n')
        LexToken(NEWLINE_TOK,'\n',4,31)
        LexToken(INTEGER,44,5,32)
        LexToken(NEWLINE_TOK,'\n',5,34)
    '''
    global Last_colonindent, debug
    global Token_dict, Word_body_symbol
    Last_colonindent = 0
    debug = debug_param
    Word_body_symbol, Token_dict = extra_arg

def set_name_value(t, name = None):
    if Word_body_symbol is None:
        if name: t.value = name
    else:
        syntax_info = t.lineno, scanner_init.get_col_line(t.lexpos)[0]
        name = name or t.value
        symbol = symbol_table.lookup(name, Word_body_symbol)
        t.value = \
          ast.ast.from_parser(
            syntax_info + syntax_info, 
            kind='word',
            label=name,
            type_id=symbol.type_id,
            symbol_id=symbol.id)
