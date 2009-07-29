# parser.py

from ucc.parser import scanner_init
from ucc.ast import ast

start = 'file'

precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('right', 'NOT'),
    ('left', '<', 'LE', 'EQ', 'NE', '>', 'GE'),
    ('left', 'ARG_LEFT_WORD'),
    ('right', 'ARG_RIGHT_WORD'),
    ('left', '+', '-'),
    ('right', '/'),
    ('left', '%'),
    ('left', '*'),
    ('left', 'BIT_OR'),
    ('left', 'BIT_XOR'),
    ('left', 'BIT_AND'),
    ('right', 'NEGATE', 'BIT_NOT'),
    ('left', ')'),
)

token_dict = {
    u'else': u'ELSE_TOK',
    u'if': u'IF',
}

def p_one_or_more_0001(p):
    r''' one_or_more_0001 : statement
    '''
    p[1].expect = 'statement'
    p[0] = (p[1],)

def p_one_or_more_0002(p):
    r''' one_or_more_0001 : one_or_more_0001 statement
    '''
    p[2].expect = 'statement'
    p[0] = p[1] + (p[2],)

def p_file_0001(p):
    r''' file : one_or_more_0001
    '''
    args = []
    args.append(p[1])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             kind='word_body', *args)

def p_zero_or_more_0001(p):
    r''' zero_or_more_0001 :
    '''
    p[0] = ()

def p_zero_or_more_0002(p):
    r''' zero_or_more_0001 : zero_or_more_0001 expr
    '''
    
    p[0] = p[1] + (p[2],)

def p_simple_statement_0001(p):
    r''' simple_statement : NAME zero_or_more_0001 NEWLINE_TOK
    '''
    args = []
    args.append(p[2])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[1], *args)

def p_statement_0001(p):
    r''' statement : simple_statement
    '''
    args = []
    args.append(p[1])
    p[0] = args[0]

def p_statement_0002(p):
    r''' statement : NAME zero_or_more_0001 series
    '''
    args = []
    args.append(p[2])
    args.append(p[3])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[1], *args)

def p_series_0001(p):
    r''' series : ':' simple_statement
    '''
    p[2].expect = 'statement'
    args = []
    args.append(p[2])
    p[0] = tuple(args)

def p_series_0002(p):
    r''' series : START_SERIES_TOK INDENT_TOK one_or_more_0001 DEINDENT_TOK
    '''
    p[0] = p[3]

def p_ellipsis_0001(p):
    r''' ellipsis_0001 :
    '''
    p[0] = ()

def p_ellipsis_0002(p):
    r''' ellipsis_0001 : ellipsis_0001 expr
    '''
    
    p[0] = p[1] + (p[2],)

def p_expr_0001(p):
    r''' expr : APPROX_NUMBER
    '''
    args = []
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             kind='approx', int1=p[1][0], int2=p[1][1], *args)

def p_expr_0002(p):
    r''' expr : CHAR
    '''
    args = []
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             kind='int', int1=p[1], *args)

def p_expr_0003(p):
    r''' expr : INTEGER
    '''
    args = []
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             kind='int', int1=p[1], *args)

def p_expr_0004(p):
    r''' expr : RATIO
    '''
    args = []
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             kind='ratio', int1=p[1][0], int2=p[1][1], *args)

def p_expr_0005(p):
    r''' expr : STRING
    '''
    args = []
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             kind='string', str1=p[1], *args)

def p_expr_0006(p):
    r''' expr : NAME
    '''
    args = []
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[1], *args)

def p_expr_0007(p):
    r''' expr : LP_TOK expr ')'
    '''
    args = []
    args.append(p[2])
    p[0] = args[0]

def p_expr_0008(p):
    r''' expr : expr '(' ellipsis_0001 ')'
    '''
    args = []
    args.extend(p[3])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[1], *args)

def p_expr_0009(p):
    r''' expr : BIT_NOT expr
    '''
    args = []
    args.append(p[2])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[1], *args)

def p_expr_0010(p):
    r''' expr : NEGATE expr
    '''
    args = []
    args.append(p[2])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[1], *args)

def p_expr_0011(p):
    r''' expr : expr BIT_AND expr
    '''
    args = []
    args.append(p[1])
    args.append(p[3])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[2], *args)

def p_expr_0012(p):
    r''' expr : expr BIT_XOR expr
    '''
    args = []
    args.append(p[1])
    args.append(p[3])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[2], *args)

def p_expr_0013(p):
    r''' expr : expr BIT_OR expr
    '''
    args = []
    args.append(p[1])
    args.append(p[3])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[2], *args)

def p_expr_0014(p):
    r''' expr : expr '*' expr
    '''
    args = []
    args.append(p[1])
    args.append(p[3])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[2], *args)

def p_expr_0015(p):
    r''' expr : expr '/' expr
    '''
    args = []
    args.append(p[1])
    args.append(p[3])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[2], *args)

def p_expr_0016(p):
    r''' expr : expr '%' expr
    '''
    args = []
    args.append(p[1])
    args.append(p[3])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[2], *args)

def p_expr_0017(p):
    r''' expr : expr '+' expr
    '''
    args = []
    args.append(p[1])
    args.append(p[3])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[2], *args)

def p_expr_0018(p):
    r''' expr : expr '-' expr
    '''
    args = []
    args.append(p[1])
    args.append(p[3])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[2], *args)

def p_expr_0019(p):
    r''' expr : ARG_RIGHT_WORD expr
    '''
    args = []
    args.append(p[2])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[1], *args)

def p_expr_0020(p):
    r''' expr : expr ARG_LEFT_WORD
    '''
    args = []
    args.append(p[1])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[2], *args)

def p_expr_0021(p):
    r''' expr : expr '<' expr
    '''
    args = []
    args.append(p[1])
    args.append(p[3])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[2], *args)

def p_expr_0022(p):
    r''' expr : expr LE expr
    '''
    args = []
    args.append(p[1])
    args.append(p[3])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[2], *args)

def p_expr_0023(p):
    r''' expr : expr EQ expr
    '''
    args = []
    args.append(p[1])
    args.append(p[3])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[2], *args)

def p_expr_0024(p):
    r''' expr : expr NE expr
    '''
    args = []
    args.append(p[1])
    args.append(p[3])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[2], *args)

def p_expr_0025(p):
    r''' expr : expr '>' expr
    '''
    args = []
    args.append(p[1])
    args.append(p[3])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[2], *args)

def p_expr_0026(p):
    r''' expr : expr GE expr
    '''
    args = []
    args.append(p[1])
    args.append(p[3])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[2], *args)

def p_expr_0027(p):
    r''' expr : NOT expr
    '''
    p[2].expect = 'cond'
    args = []
    args.append(p[2])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[1], *args)

def p_expr_0028(p):
    r''' expr : expr AND expr
    '''
    p[1].expect = 'cond'
    p[3].expect = 'cond'
    args = []
    args.append(p[1])
    args.append(p[3])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[2], *args)

def p_expr_0029(p):
    r''' expr : expr OR expr
    '''
    p[1].expect = 'cond'
    p[3].expect = 'cond'
    args = []
    args.append(p[1])
    args.append(p[3])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[2], *args)

def p_sub_rule_0001_0001(p):
    r''' sub_rule_0001 : ELSE_TOK series
    '''
    args = []
    args.append(p[2])
    p[0] = args[0]

def p_optional_0001(p):
    r''' optional_0001 :
    '''
    p[0] = None

def p_optional_0002(p):
    r''' optional_0001 : sub_rule_0001
    '''
    
    p[0] = p[1]

def p_statement_0003(p):
    r''' statement : IF expr series optional_0001
    '''
    p[2].expect = 'condition'
    args = []
    args.append(p[2])
    args.append(p[3])
    args.append(p[4])
    p[0] = ast.ast.from_parser(
             scanner_init.get_syntax_position_info(p),
             word=p[1], *args)

def p_error(t):
    if t is None:
        raise SyntaxError("invalid syntax",
                          scanner_init.syntaxerror_params())
    else:
        raise SyntaxError("invalid syntax",
                          scanner_init.syntaxerror_params(t))

tokens = ['AND', 'APPROX_NUMBER', 'ARG_LEFT_WORD', 'ARG_RIGHT_WORD', 'BIT_AND',
          'BIT_NOT', 'BIT_OR', 'BIT_XOR', 'CHAR', 'DEINDENT_TOK', u'ELSE_TOK',
          'EQ', 'GE', u'IF', 'INDENT_TOK', 'INTEGER', 'LB_TOK', 'LE', 'LP_TOK',
          'NAME', 'NE', 'NEGATE', 'NEWLINE_TOK', 'NOT', 'OR', 'RATIO',
          'START_SERIES_TOK', 'STRING']

def init():
    pass

