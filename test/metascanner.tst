# metascanner.tst

>>> from ucc.parser import metascanner, scanner_init

>>> scanner_init.tokenize(metascanner, 'hi MOM DAD_TOK')
LexToken(NONTERMINAL,'hi',1,0)
LexToken(TOKEN,'MOM',1,3)
LexToken(TOKEN_IGNORE,'DAD_TOK',1,7)

>>> scanner_init.tokenize(metascanner, '[hi]\n | (mom)... # ignore this')
LexToken(TUPLE_NONTERMINAL,'hi',1,0)
LexToken(|,'|',2,6)
LexToken((,'(',2,8)
LexToken(NONTERMINAL,'mom',2,9)
LexToken(),')',2,12)
LexToken(ELLIPSIS,'...',2,13)

>>> scanner_init.tokenize(metascanner, 'hi\n  mom\n dad')
LexToken(NONTERMINAL,'hi',1,0)
LexToken(NONTERMINAL,'mom',2,5)
LexToken(NONTERMINAL,'dad',3,10)

>>> scanner_init.tokenize(metascanner, 'hi:\n    mom\ndad')
LexToken(NONTERMINAL,'hi',1,0)
LexToken(:,':',1,2)
LexToken(NONTERMINAL,'mom',2,8)
LexToken(NEWLINE_TOK,'\nd',2,11)
LexToken(NONTERMINAL,'dad',3,12)

>>> scanner_init.tokenize(metascanner, r"'h' as foo=python 'code',")
LexToken(CHAR_TOKEN,"'h'",1,0)
LexToken(AS_TOK,'as',1,4)
LexToken(NONTERMINAL,'foo',1,7)
LexToken(PYTHON_CODE,"python 'code'",1,11)
LexToken(,,',',1,24)

>>> scanner_init.tokenize(metascanner, r"foo=python 'a, code')")
LexToken(NONTERMINAL,'foo',1,0)
LexToken(PYTHON_CODE,"python 'a, code'",1,4)
LexToken(),')',1,20)

>>> scanner_init.tokenize(metascanner, r'foo=python "(a,) code",')
LexToken(NONTERMINAL,'foo',1,0)
LexToken(PYTHON_CODE,'python "(a,) code"',1,4)
LexToken(,,',',1,22)

