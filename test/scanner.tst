# scanner.tst

>>> from ucc.parser import scanner
>>> scanner.tokenize(scanner, {}, r'hi mom')
LexToken(NAME_TOK,'hi',1,0)
LexToken(NAME_TOK,'mom',1,3)
