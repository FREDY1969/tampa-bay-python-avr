# metaparser.py

"""This parses the metasyntax (used to define parsers).

See the METASYNTAX file for the grammar that this recognizes.

See http://www.dabeaz.com/ply/ply.html for syntax of grammer definitions used
here.
""" 



import string
import sys

from ucc.parser import metascanner, scanner_init
from ucc.database import ast, crud

tokens = metascanner.tokens

Tokens_used = set()
Output_file = sys.stdout

def p_file(p):
    ''' file : file2
             | file2 rule
    '''
    p[0] = Tokens_used

def p_none(p):
    ''' file2 :
              | file2 NEWLINE_TOK
              | file2 rule NEWLINE_TOK
        param_list_opt :
    '''
    p[0] = None

def p_first(p):
    ''' word : parameterized_word
        parameters_opt : parameters
        param_list_opt : param_list
        parameterized_word : sub_rule
        sub_rule : simple_word
    '''
    p[0] = p[1]

def p_empty_tuple(p):
    ''' production :
    '''
    p[0] = ()

def p_append(p):
    ''' production : production word
    '''
    p[0] = p[1] + (p[len(p) - 1],)

def p_alternatives_1(p):
    ''' alternatives : production
    '''
    p[0] = ((p[1], p.lineno(1), p.lexpos(1)),)

def p_alternatives_n(p):
    ''' alternatives : alternatives '|' production
    '''
    p[0] = p[1] + ((p[len(p) - 1], p.lineno(3), p.lexpos(3)),)

def p_rule1(p):
    ''' rule : NONTERMINAL param_list_opt ':' alternatives
    '''
    gen_alternatives(p[1], p[4], normal_wrapup, p[2])

def gen_alternatives(rule_name, alternatives, wrapup_fn, param_list = None):
    for words, lineno, lexpos in alternatives:
        p_fn_name = crud.gensym('p_' + rule_name)
        output("""
            def $fn_name(p):
                r''' $rule_name : $production
                '''
            """,
            output_file = Output_file,
            fn_name = p_fn_name, rule_name = rule_name,
            production = ' '.join(word[0] for word in words))
        prep = []
        args = []
        last_arg = None
        tuple_offset = None
        has_ellipsis = False
        if param_list is not None:
            fn_word_params = param_list
            fn_word_offset = None
        else:
            fn_word_params = None
            fn_word_offset = None
        for i, (rule_text, type, offset, prep_code, params) in enumerate(words):
            if prep_code: prep.append(prep_code % {'offset': offset + i + 1})
            if type == 'fn_word':
                if fn_word_params is not None:
                    scanner_init.syntaxerror(
                      "duplicate function words in production",
                      lineno = lineno, lexpos = lexpos)
                fn_word_offset = offset + i + 1
                fn_word_params = params
            else:
                assert not params, "non function word has parameters"
                if type == 'ignore':
                    pass
                elif type == 'single_arg':
                    args.append('args.append(p[%d])' % (offset + i + 1))
                    last_arg = offset + i + 1
                elif type == 'tuple':
                    args.append('args.append(p[%d])' % (offset + i + 1))
                    if tuple_offset is not None:
                        if not has_ellipsis:
                            tuple_offset = 'dup'
                    else:
                        tuple_offset = i
                elif type == 'ellipsis':
                    args.append('args.extend(p[%d])' % (offset + i + 1))
                    has_ellipsis = True

        if prep:
            print('\n'.join('    ' + p for p in prep), file=Output_file)

        wrapup_fn(fn_word_params, fn_word_offset, args, last_arg, tuple_offset,
                  has_ellipsis, lineno, lexpos)
        print(file=Output_file)

def normal_wrapup(fn_word_params, fn_word_offset, args, last_arg, tuple_offset,
                  has_ellipsis, lineno, lexpos):
    print("    args = []", file=Output_file)
    for arg in args: print("    " + arg, file=Output_file)
    if fn_word_params is None:
        if not has_ellipsis and len(args) == 1:
            print("    p[0] = args[0]", file=Output_file)
        else:
            print("    p[0] = tuple(args)", file=Output_file)
    else:
        if fn_word_params:
            output("""
              p[0] = ast.ast.from_parser(
                       scanner_init.get_syntax_position_info(p),
                       $kw_args, *args)
              """,
              output_file = Output_file,
              target_indent = 4,
              kw_args = ', '.join("%s=%s" %
                                     (key, value % {'offset': fn_word_offset})
                                     for key, value in fn_word_params))
        elif fn_word_offset is None:
            scanner_init.syntaxerror(
              "empty parameter list on nonterminal declaration",
              lineno = lineno, lexpos = lexpos)
        else:
            output("""
              p[0] = ast.ast.from_parser(
                       scanner_init.get_syntax_position_info(p),
                       p[$offset], *args)
              """,
              output_file = Output_file,
              target_indent = 4,
              offset = fn_word_offset)

def wrapup_tuple(fn_word_params, fn_word_offset, args, last_arg, tuple_offset,
                 has_ellipsis, lineno, lexpos):
    if fn_word_params is not None:
        print("    args = []", file=Output_file)
        for arg in args: print("    " + arg, file=Output_file)
        if fn_word_params:
            output("""
              p[0] = (ast.ast.from_parser(
                        scanner_init.get_syntax_position_info(p),
                        $kw_args, *args),)
              """,
              output_file = Output_file,
              target_indent = 4,
              kw_args = ', '.join("%s=%s" %
                                    (key, value % {'offset': fn_word_offset})
                                    for key, value in fn_word_params))
        else:
            output("""
              p[0] = (ast.ast.from_parser(
                        scanner_init.get_syntax_position_info(p),
                        p[$offset], *args),)
              """,
              output_file = Output_file,
              target_indent = 4,
              offset = fn_word_offset)
    elif has_ellipsis:
        scanner_init.syntaxerror(
          "ellipsis in production without function word",
          lineno = lineno, lexpos = lexpos)
    elif tuple_offset == 'dup':
        scanner_init.syntaxerror("duplicate tuples in production",
                                 lineno = lineno, lexpos = lexpos)
    elif tuple_offset is None:
        # Make a singleton tuple out of a single argument.
        if len(args) == 1:
            print("    args = []", file=Output_file)
            print('    ' + args[0], file=Output_file)
            print("    p[0] = tuple(args)", file=Output_file)
        else:
            scanner_init.SyntaxError("no tuple in production")
    else:
        print("    p[0] = p[%d]" % (tuple_offset + 1), file=Output_file)

def p_rule2(p):
    ''' rule : TUPLE_NONTERMINAL ':' alternatives
    '''
    gen_alternatives(p[1], p[3], wrapup_tuple)

Optional_rules = {}

def p_opt_word(p):
    ''' word : sub_rule '?'
    '''
    rule_name = Optional_rules.get(p[1])
    if rule_name is None:
        rule_name = crud.gensym('optional')
        Optional_rules[p[1]] = rule_name
        rule_text, type, offset, prep_code, params = p[1]
        p_fn_name_0, p_fn_name_n = \
          crud.gensym('p_optional'), crud.gensym('p_optional')
        output("""
            def $fn_name1(p):
                r''' $rule_name :
                '''
                p[0] = None

            def $fn_name2(p):
                r''' $rule_name : $production
                '''
                $prep_code
                p[0] = p[$offset]

            """,
            output_file = Output_file,
            fn_name1 = p_fn_name_0,
            rule_name = rule_name,
            fn_name2 = p_fn_name_n,
            production = rule_text,
            prep_code = prep_code % {'offset': offset + 1} if prep_code else '',
            offset = offset + 1)
    p[0] = rule_name, type, 0, None, None

One_or_more_rules = {}

def p_one_or_more_word(p):
    ''' word : sub_rule '+'
    '''
    rule_name = One_or_more_rules.get(p[1])
    if rule_name is None:
        rule_name = crud.gensym('one_or_more')
        One_or_more_rules[p[1]] = rule_name
        rule_text, type, offset, prep_code, params = p[1]
        p_fn_name_1, p_fn_name_n = \
          crud.gensym('p_one_or_more'), crud.gensym('p_one_or_more')
        prep = prep_code % {'offset': offset + 2} if prep_code else ''
        output("""
            def $fn_name(p):
                r''' $rule_name : $production
                '''
                $prep_code
                p[0] = (p[$offset],)

            """,
            output_file = Output_file,
            fn_name = p_fn_name_1,
            rule_name = rule_name,
            production = rule_text,
            prep_code = prep_code % {'offset': offset + 1} if prep_code else '',
            offset = offset + 1)
        output("""
            def $fn_name(p):
                r''' $rule_name : $rule_name $production
                '''
                $prep_code
                p[0] = p[1] + (p[$offset],)

            """,
            output_file = Output_file,
            fn_name = p_fn_name_n,
            rule_name = rule_name,
            production = rule_text,
            prep_code = prep_code % {'offset': offset + 2} if prep_code else '',
            offset = offset + 2)
    p[0] = rule_name, 'tuple', 0, None, None

Zero_or_more_rules = {}

def p_zero_or_more_word(p):
    ''' word : sub_rule '*'
    '''
    rule_name = Zero_or_more_rules.get(p[1])
    if rule_name is None:
        rule_name = crud.gensym('zero_or_more')
        Zero_or_more_rules[p[1]] = rule_name
        rule_text, type, offset, prep_code, params = p[1]
        p_fn_name_0, p_fn_name_n = \
          crud.gensym('p_zero_or_more'), crud.gensym('p_zero_or_more')
        output("""
            def $fn_name1(p):
                r''' $rule_name :
                '''
                p[0] = ()

            def $fn_name2(p):
                r''' $rule_name : $rule_name $production
                '''
                $prep_code
                p[0] = p[1] + (p[$offset],)

            """,
            output_file = Output_file,
            fn_name1 = p_fn_name_0,
            rule_name = rule_name,
            fn_name2 = p_fn_name_n,
            production = rule_text,
            prep_code = prep_code % {'offset': offset + 2} if prep_code else '',
            offset = offset + 2)
    p[0] = rule_name, 'tuple', 0, None, None

Ellipsis_rules = {}

def p_word_ellipsis(p):
    ''' word : sub_rule ELLIPSIS
    '''
    rule_name = Ellipsis_rules.get(p[1])
    if rule_name is None:
        rule_name = crud.gensym('ellipsis')
        Ellipsis_rules[p[1]] = rule_name
        rule_text, type, offset, prep_code, params = p[1]
        p_fn_name_0, p_fn_name_n = \
          crud.gensym('p_ellipsis'), crud.gensym('p_ellipsis')
        output("""
            def $fn_name1(p):
                r''' $rule_name :
                '''
                p[0] = ()

            def $fn_name2(p):
                r''' $rule_name : $rule_name $production
                '''
                $prep_code
                p[0] = p[1] + (p[$offset],)

            """,
            output_file = Output_file,
            fn_name1 = p_fn_name_0,
            rule_name = rule_name,
            fn_name2 = p_fn_name_n,
            production = rule_text,
            prep_code = prep_code % {'offset': offset + 2} if prep_code else '',
            offset = offset + 2)
    p[0] = rule_name, 'ellipsis', 0, None, None

def p_parameterized_word(p):
    ''' parameterized_word : simple_word param_list
    '''
    rule_text, type, offset, prep_code, params = p[1]
    if params:
        scanner_init.syntaxerror("duplicate initialization parameters",
                                 lineno=p.lineno(2), lexpos=p.lexpos(2))
    param_list = p[2]
    p[0] = rule_text, 'fn_word', offset, prep_code, param_list

def p_sub_rule(p):
    ''' sub_rule : simple_word AS_TOK NONTERMINAL
    '''
    rule_text, type, offset, prep_code, params = p[1]
    if prep_code:
        prep_code += '\n    '
    else:
        prep_code = ''
    p[0] = rule_text, type, offset, \
           prep_code + "p[%(offset)d].expect = '" + p[3] + "'", \
           params

def p_sub_rule2(p):
    ''' sub_rule : '(' alternatives ')'
    '''
    rule_name = crud.gensym('sub_rule')
    gen_alternatives(rule_name, p[2], normal_wrapup)
    p[0] = rule_name, 'single_arg', 0, None, None

def p_token_ignore(p):
    ''' simple_word : TOKEN_IGNORE
    '''
    global Tokens_used
    Tokens_used.add(p[1])
    p[0] = p[1], 'ignore', 0, None, None

def p_char_token(p):
    ''' simple_word : CHAR_TOKEN
    '''
    p[0] = p[1], 'ignore', 0, None, None

def p_token(p):
    ''' simple_word : TOKEN
    '''
    global Tokens_used
    Tokens_used.add(p[1])
    p[0] = p[1], 'single_arg', 0, None, None

def p_nonterminal(p):
    ''' simple_word : NONTERMINAL
    '''
    p[0] = p[1], 'single_arg', 0, None, None

def p_tuple_simple_word(p):
    ''' simple_word : TUPLE_NONTERMINAL
    '''
    p[0] = p[1], 'tuple', 0, None, None

def p_param_list(p):
    ''' param_list : START_PARAMS parameters_opt ')'
    '''
    p[0] = p[2]

def p_no_parameters_opt(p):
    ''' parameters_opt : 
    '''
    p[0] = ()

def p_parameters1(p):
    ''' parameters : parameter
    '''
    p[0] = (p[1],)

def p_parametersn(p):
    ''' parameters : parameters ',' parameter
    '''
    p[0] = p[1] + (p[3],)

def p_parameter(p):
    ''' parameter : NONTERMINAL PYTHON_CODE
    '''
    p[0] = (p[1], p[2])

def p_error(t):
    if t is None:
        raise SyntaxError("invalid syntax", scanner_init.syntaxerror_params())
    else:
        raise SyntaxError("invalid syntax", scanner_init.syntaxerror_params(t))

def output(str, target_indent = 0, output_file = sys.stdout, **kws):
    output_file.write(string.Template(strip_indent(str, target_indent))
                            .substitute(kws))

def strip_indent(str, target_indent = 0):
    r'''Strip initial indent off of all lines in str.

    >>> strip_indent('    hi\n    mom\n        indented\n')
    'hi\nmom\n    indented\n'
    >>> strip_indent('\n    hi\n    mom\n        indented\n')
    'hi\nmom\n    indented\n'
    >>> strip_indent('\n\n    hi\n    mom\n        indented\n')
    '\nhi\nmom\n    indented\n'
    >>> strip_indent('\n    hi\n    mom\n        indented\n', 4)
    '    hi\n    mom\n        indented\n'
    >>> strip_indent('\nhi\nmom\n    indented\n', 4)
    '    hi\n    mom\n        indented\n'
    >>> strip_indent('\n\nhi\nmom\n    indented\n', 4)
    '\n    hi\n    mom\n        indented\n'
    '''
    assert '\t' not in str, "tabs not allowed in output strings"
    str = str.replace('\r', '')
    if str[0] == '\n': str = str[1:]
    stripped = str.lstrip()
    indent = len(str) - len(stripped)
    last_nl = str.rfind('\n', 0, indent) + 1
    if last_nl > 0:
        indent -= last_nl
        stripped = str
    else: # no '\n'
        stripped = ' ' * target_indent + stripped
    return stripped.replace('\n' + ' ' * indent, '\n' + ' ' * target_indent) \
                   .rstrip(' ')

def init():
    global Tokens_used, One_or_more_rules, Zero_or_more_rules, Ellipsis_rules
    Tokens_used = set()
    One_or_more_rules = {}
    Zero_or_more_rules = {}
    Ellipsis_rules = {}
