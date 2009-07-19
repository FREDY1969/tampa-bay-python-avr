# metaparser.tst

>>> from ucc.parser import metaparser, parser_init, metascanner

>>> parser_init.test(metaparser, metascanner, "hi: mom() DAD_TOK")
<BLANKLINE>
def p_hi_0001(p):
    r''' hi : mom DAD_TOK
    '''
    args = []
    p[0] = ast.ast(p[1], p[len(p) - 1], word_id=p[1], *args)
None

>>> parser_init.test(metaparser, metascanner, "hi: mom() dad")
<BLANKLINE>
def p_hi_0002(p):
    r''' hi : mom dad
    '''
    args = []
    args.append(p[2])
    p[0] = ast.ast(p[1], p[len(p) - 1], word_id=p[1], *args)
None

>>> parser_init.test(metaparser, metascanner, "hi: mom() '+' dad")
<BLANKLINE>
def p_hi_0003(p):
    r''' hi : mom '+' dad
    '''
    args = []
    args.append(p[3])
    p[0] = ast.ast(p[1], p[len(p) - 1], word_id=p[1], *args)
None

>>> parser_init.test(metaparser, metascanner, "hi: mom '+'() dad")
<BLANKLINE>
def p_hi_0004(p):
    r''' hi : mom '+' dad
    '''
    args = []
    args.append(p[1])
    args.append(p[3])
    p[0] = ast.ast(p[1], p[len(p) - 1], word_id=p[2], *args)
None

>>> parser_init.test(metaparser, metascanner, "hi: mom dad()")
<BLANKLINE>
def p_hi_0005(p):
    r''' hi : mom dad
    '''
    args = []
    args.append(p[1])
    p[0] = ast.ast(p[1], p[len(p) - 1], word_id=p[2], *args)
None

>>> parser_init.test(metaparser, metascanner, "hi: mom as cond dad()")
<BLANKLINE>
def p_hi_0006(p):
    r''' hi : mom dad
    '''
    p[1].expect = 'cond'
    args = []
    args.append(p[1])
    p[0] = ast.ast(p[1], p[len(p) - 1], word_id=p[2], *args)
None

>>> parser_init.test(metaparser, metascanner, "hi(kind='foobar'): mom dad")
<BLANKLINE>
def p_hi_0007(p):
    r''' hi : mom dad
    '''
    args = []
    args.append(p[1])
    args.append(p[2])
    p[0] = ast.ast(p[1], p[len(p) - 1], kind='foobar', *args)
None

>>> parser_init.test(metaparser, metascanner, "hi: mom(foo=1,bar='baz') DAD")
<BLANKLINE>
def p_hi_0008(p):
    r''' hi : mom DAD
    '''
    args = []
    args.append(p[2])
    p[0] = ast.ast(p[1], p[len(p) - 1], foo=1, bar='baz', *args)
None

>>> parser_init.test(metaparser, metascanner,
...                  "hi: mom(w_id=p[%s]) [dad]")
<BLANKLINE>
def p_hi_0009(p):
    r''' hi : mom dad
    '''
    args = []
    args.append(p[2])
    p[0] = ast.ast(p[1], p[len(p) - 1], w_id=p[1], *args)
None

>>> parser_init.test(metaparser, metascanner, "hi: mom() | dad()")
<BLANKLINE>
def p_hi_0010(p):
    r''' hi : mom
    '''
    args = []
    p[0] = ast.ast(p[1], p[len(p) - 1], word_id=p[1], *args)
<BLANKLINE>
def p_hi_0011(p):
    r''' hi : dad
    '''
    args = []
    p[0] = ast.ast(p[1], p[len(p) - 1], word_id=p[1], *args)
None

>>> parser_init.test(metaparser, metascanner, "hi: mom() dad?")
<BLANKLINE>
def p_optional_0001(p):
    r''' optional_0001 :
    '''
    p[0] = None
<BLANKLINE>
def p_optional_0002(p):
    r''' optional_0001 : dad
    '''
<BLANKLINE>
    p[0] = p[1]
<BLANKLINE>
def p_hi_0012(p):
    r''' hi : mom optional_0001
    '''
    args = []
    args.append(p[2])
    p[0] = ast.ast(p[1], p[len(p) - 1], word_id=p[1], *args)
None

>>> parser_init.test(metaparser, metascanner, "hi: mom() dad+")
<BLANKLINE>
def p_one_or_more_0001(p):
    r''' one_or_more_0001 : dad
    '''
<BLANKLINE>
    p[0] = (p[1],)
<BLANKLINE>
def p_one_or_more_0002(p):
    r''' one_or_more_0001 : one_or_more_0001 dad
    '''
<BLANKLINE>
    p[0] = p[1] + (p[2],)
<BLANKLINE>
def p_hi_0013(p):
    r''' hi : mom one_or_more_0001
    '''
    args = []
    args.append(p[2])
    p[0] = ast.ast(p[1], p[len(p) - 1], word_id=p[1], *args)
None

>>> parser_init.test(metaparser, metascanner, "hi: mom() dad*")
<BLANKLINE>
def p_zero_or_more_0001(p):
    r''' zero_or_more_0001 :
    '''
    p[0] = ()
<BLANKLINE>
def p_zero_or_more_0002(p):
    r''' zero_or_more_0001 : zero_or_more_0001 dad
    '''
<BLANKLINE>
    p[0] = p[1] + (p[2],)
<BLANKLINE>
def p_hi_0014(p):
    r''' hi : mom zero_or_more_0001
    '''
    args = []
    args.append(p[2])
    p[0] = ast.ast(p[1], p[len(p) - 1], word_id=p[1], *args)
None

>>> parser_init.test(metaparser, metascanner, "hi: mom() dad...")
<BLANKLINE>
def p_ellipsis_0001(p):
    r''' ellipsis_0001 :
    '''
    p[0] = ()
<BLANKLINE>
def p_ellipsis_0002(p):
    r''' ellipsis_0001 : ellipsis_0001 dad
    '''
<BLANKLINE>
    p[0] = p[1] + (p[2],)
<BLANKLINE>
def p_hi_0015(p):
    r''' hi : mom ellipsis_0001
    '''
    args = []
    args.extend(p[2])
    p[0] = ast.ast(p[1], p[len(p) - 1], word_id=p[1], *args)
None

