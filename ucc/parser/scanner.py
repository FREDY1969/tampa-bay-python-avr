# scanner.py

# See http://www.dabeaz.com/ply/ply.html for syntax of grammer definitions.

from __future__ import with_statement, division

import math
from ucc.parser import scanner_init

debug = 0

states = (
    ('colonindent', 'exclusive'),
    ('indent', 'exclusive'),
    ('string', 'exclusive'),
)

tokens = (
    'APPROX_NUMBER_TOK',
    'CHAR_TOK',
    'DEINDENT_TOK',
    'INDENT_TOK',
    'INTEGER_TOK',
    'LB_TOK',
    'LP_TOK',
    'NAME_TOK',
    'NEWLINE_TOK',
    'RATIO_TOK',
    'START_SERIES_TOK',
    'STRING_TOK',
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

Last_colonindent = 0

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

def t_CHAR_TOK(t):
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
    t.type = 'CHAR_TOK'
    return t

def t_hex_char_tok(t):
    r"'\\[xX][0-9a-fA-F]{2}'"
    t.value = int(t.value[3:-1], 16)
    t.type = 'CHAR_TOK'
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

def t_string_STRING_TOK(t):
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

def t_INTEGER_TOK(t):
    r'''[0-9]+
        (?=[]) \r\n])   # followed by ], ), space or newline
    '''
    t.value = int(t.value)
    return t

def t_hex_INTEGER_TOK(t):
    r'''0[xX][0-9]+
        (?=[]) \r\n])   # followed by ], ), space or newline
    '''
    t.value = int(t.value, 16)
    t.type = 'INTEGER_TOK'
    return t

def t_RATIO_TOK(t):
    r'''[0-9]+/[0-9]+   # ratio
        (?=[]) \r\n])   # followed by ], ), space or newline
    '''
    slash = t.value.index('/')
    t.value = (int(t.value[:slash]), int(t.value[slash+1:]))
    return t

def t_ratio_2(t):
    r'''[0-9]+
        \.[0-9]+        # decimal point
        /[0-9]+         # denominator
        (?=[]) \r\n])   # followed by ], ), space or newline
    '''
    dot = t.value.index('.')
    slash = t.value.index('/')
    denominator = int(t.value[slash+1:])
    t.value = (int(t.value[:dot]) * denominator + int(t.value[dot+1:slash]),
               denominator)
    t.type = 'RATIO_TOK'
    return t

def t_ratio_3(t):
    r'''[0-9]+
        \.[0-9]+        # decimal point
        /               # implied denominator
        (?=[]) \r\n])   # followed by ], ), space or newline
    '''
    dot = t.value.index('.')
    denominator = 10**(len(t.value) - dot - 2)
    t.value = (int(t.value[:dot]) * denominator + int(t.value[dot + 1:-1]),
               denominator)
    t.type = 'RATIO_TOK'
    return t

def t_ratio_4(t):
    r'''\.[0-9]+        # decimal point
        /               # implied denominator
        (?=[]) \r\n])   # followed by ], ), space or newline
    '''
    denominator = 10**(len(t.value) - 2)
    t.value = (int(t.value[1:-1]), denominator)
    t.type = 'RATIO_TOK'
    return t

def t_hex_RATIO_TOK(t):
    r'''0[xX][0-9a-fA-F]+/[0-9a-fA-F]+ # ratio
        (?=[]) \r\n])                  # followed by ], ), space or newline
    '''
    slash = t.value.index('/')
    t.value = (int(t.value[:slash], 16), int(t.value[slash+1:], 16))
    t.type = 'RATIO_TOK'
    return t

def t_hex_ratio_2(t):
    r'''0[xX][0-9a-fA-F]+
        \.[0-9a-fA-F]+        # decimal point
        /[0-9a-fA-F]+         # denominator
        (?=[]) \r\n])         # followed by ], ), space or newline
    '''
    dot = t.value.index('.')
    slash = t.value.index('/')
    denominator = int(t.value[slash + 1:], 16)
    t.value = (int(t.value[:dot], 16) * denominator +
                 int(t.value[dot + 1:slash], 16),
               denominator)
    t.type = 'RATIO_TOK'
    return t

def t_hex_ratio_3(t):
    r'''0[xX][0-9a-fA-F]+
        \.[0-9a-fA-F]+        # decimal point
        /                     # implied denominator
        (?=[]) \r\n])         # followed by ], ), space or newline
    '''
    dot = t.value.index('.')
    denominator = 16**(len(t.value) - dot - 2)
    t.value = (int(t.value[:dot], 16) * denominator +
                 int(t.value[dot + 1:-1], 16),
               denominator)
    t.type = 'RATIO_TOK'
    return t

def t_hex_ratio_4(t):
    r'''0[xX]
        \.[0-9a-fA-F]+        # decimal point
        /                     # implied denominator
        (?=[]) \r\n])         # followed by ], ), space or newline
    '''
    denominator = 16**(len(t.value) - 4)
    t.value = (int(t.value[3:-1], 16), denominator)
    t.type = 'RATIO_TOK'
    return t

def t_APPROX_NUMBER_TOK(t):
    # All decimal forms with a '.':
    r'''(?: [0-9]+ \.[0-9]* | \.[0-9]+ )
        (?: ~[0-9] )?
        (?: [eE] [+-]?[0-9]+ )?
        (?=[]) \r\n])    # followed by ], ), space or newline
    '''
    t.value = approx(t.value.lower())
    return t

def t_approx_2(t):
    # All decimal forms without a '.':
    r'''[0-9]+ (?: (?: ~[0-9] )? [eE] [+-]?[0-9]+ | ~[0-9] )
        (?=[]) \r\n])    # followed by ], ), space or newline
    '''
    t.value = approx(t.value.lower())
    t.type = 'APPROX_NUMBER_TOK'
    return t

def t_hex_APPROX_NUMBER_TOK(t):
    # All hex forms with a '.':
    r'''0[xX] (?: [0-9a-fA-F]+ \.[0-9a-fA-F]* | \.[0-9a-fA-F]+ )
              (?: ~[0-9a-fA-F] )?
              (?: [xX] [+-]?[0-9]+ )?
        (?=[]) \r\n])    # followed by ], ), space or newline
    '''
    t.value = approx(t.value[2:].lower(), 16)
    t.type = 'APPROX_NUMBER_TOK'
    return t

def t_hex_approx_2(t):
    # All hex forms without a '.':
    r'''0[xX] [0-9a-fA-F]+
        (?: (?: ~[0-9a-fA-F] )? [xX] [+-]?[0-9]+
          | ~[0-9a-fA-F] )
        (?=[]) \r\n])    # followed by ], ), space or newline
    '''
    t.value = approx(t.value[2:].lower(), 16)
    t.type = 'APPROX_NUMBER_TOK'
    return t

def t_NAME_TOK(t):
    r'''[^[( \r\n"'#-]     # first character
        [^[( \r\n]*        # middle characters
        [^])[( \r\n:]      # last character
    '''
    if t.value in Word_dict:
        t.value = Word_dict[t.value]
        t.type = t.value.token
    return t

def t_NAME_TOK_1(t):
    r'''[^])[( \r\n:"'#-]
        (?=[][() \r\n])    # followed by [, ], (, ), space or newline
    '''
    if t.value in Word_dict:
        t.value = Word_dict[t.value]
        t.type = t.value.token
    else:
        t.type = 'NAME_TOK'
    return t

def t_negate(t):
    r'''-
        (?=[^]) \r\n])  # followed by name, number, string, -, ( or [
    '''
    if 'negate' in Word_dict:
        t.value = Word_dict['negate']
        t.type = t.value.token
    else:
        t.value = 'negate'
        t.type = 'NAME_TOK'
    return t

def t_minus(t):
    r'''-
        (?=[]) \r\n])   # followed by space, newline, ] or )
    '''
    if '-' in Word_dict:
        t.value = Word_dict['-']
        t.type = t.value.token
    else:
        t.value = '-'
        t.type = 'NAME_TOK'
    return t

def t_ANY_error(t):
    raise SyntaxError("Scanner error: possible illegal character %r" %
                        t.value[0],
                      scanner_init.syntaxerror_params())

def approx(s, base = 10):
    r'''Return the approx value for s as (integer, binary_pt).

    The format for s is: digit* .digit* ~digit e[+-]?digit*
    Note that this does not accept negative numbers.

    >>> approx('123.')
    (123, 0)
    >>> approx('123~1')
    (123, 0)
    >>> approx('122~1')
    (61, 1)
    >>> approx('123.5')
    (1976, -4)
    >>> approx('123.5~1')
    (988, -3)
    >>> approx('123~1e1')
    (77, 4)
    >>> approx('123e1')
    (308, 2)
    >>> approx('123~1e-1')
    (197, -4)
    >>> approx('123e-1')
    (197, -4)
    '''
    dot = s.find('.')
    tilde = s.find('~')
    e = s.find('e' if base == 10 else 'x')
    if e < 0:
        exp = 0
        e = len(s)
    else:
        exp = int(s[e + 1:])
    if tilde < 0:
        prec = base // 2
        prec_place = 1
        tilde = e
    else:
        prec = int(s[tilde + 1:e], base)
        prec_place = 0
    if dot < 0:
        decimal_places = 0
        n = int(s[:tilde], base)
    else:
        decimal_places = tilde - dot - 1
        if dot > 0:
            n = int(s[:dot], base) * base**decimal_places
        else:
            n = 0
        if decimal_places:
            n += int(s[dot + 1:tilde], base)

    number = n * base**(exp - decimal_places)
    precision = prec / base**(decimal_places + prec_place - exp)

    #print "n", n, "decimal_places", decimal_places, \
    #      "prec", prec, "prec_place", prec_place, "exp", exp
    #
    #print "number", number
    #print "precision", precision

    # We want the greatest integer binary_pt such that:
    #
    #    (i - 0.5) * 2**binary_pt >= number - precision
    #    (i + 0.5) * 2**binary_pt <= number + precision
    #
    # for some integer, i.
    #
    # This can not be solved directly.
    #
    # So we'll take an iterative approach starting with:
    #
    #    2**binary_pt * 0.5 == precision
    #
    # Solving for binary_pt:
    #
    #    binary_pt = log2(2 * precision)
    #    binary_pt = log2(precision) + 1

    target = math.log(precision) / math.log(2) + 1
    binary_pt = int(math.ceil(target))
    smallest_reject = None
    largest_ok = None

    while smallest_reject is None or largest_ok is None:
        i = int(round(number / 2**binary_pt))
        if (i - 0.5) * 2**binary_pt >= number - precision and \
           (i + 0.5) * 2**binary_pt <= number + precision:
            largest_ok = i, binary_pt
            binary_pt += 1
        else:
            smallest_reject = binary_pt
            binary_pt -= 1
    return largest_ok

def init(debug_param, word_dict = {}):
    r'''
        >>> import scanner
        >>> import scanner_init
        >>> scanner_init.tokenize(scanner, '22\n')
        LexToken(INTEGER_TOK,22,1,0)
        LexToken(NEWLINE_TOK,'\n',1,2)
        >>> scanner_init.tokenize(scanner,
        ...                       '# comment1\n\n    \n    # comment2\n44\n')
        LexToken(NEWLINE_TOK,'\n',4,31)
        LexToken(INTEGER_TOK,44,5,32)
        LexToken(NEWLINE_TOK,'\n',5,34)
    '''
    global Last_colonindent, debug
    global Word_dict
    Last_colonindent = 0
    debug = debug_param
    Word_dict = word_dict

