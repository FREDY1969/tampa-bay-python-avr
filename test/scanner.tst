# scanner.tst

>>> from ucc.parser import scanner, scanner_init

>>> scanner_init.tokenize(scanner, 'hi mom')
LexToken(NAME,'hi',1,0)
LexToken(NAME,'mom',1,3)

>>> scanner_init.tokenize(scanner, 'hi\n mom')
LexToken(NAME,'hi',1,0)
LexToken(NAME,'mom',2,4)

>>> scanner_init.tokenize(scanner, 'hi\n  mom\n dad')
LexToken(NAME,'hi',1,0)
LexToken(NAME,'mom',2,5)
LexToken(NAME,'dad',3,10)

>>> scanner_init.tokenize(scanner, 'hi:\n    mom\ndad')
LexToken(NAME,'hi',1,0)
LexToken(START_SERIES_TOK,':\n',1,2)
LexToken(INDENT_TOK,'\n    ',2,3)
LexToken(NAME,'mom',2,8)
LexToken(NEWLINE_TOK,'\n',2,11)
LexToken(DEINDENT_TOK,'\n',3,11)
LexToken(NAME,'dad',3,12)

>>> scanner_init.tokenize(scanner, r"'h' '\n' '\N' '\x01' '\X10'")
LexToken(CHAR,104,1,0)
LexToken(CHAR,10,1,4)
LexToken(CHAR,10,1,9)
LexToken(CHAR,1,1,14)
LexToken(CHAR,16,1,21)

>>> scanner_init.tokenize(scanner, r'"h\n\N\x01\X10"')
LexToken(STRING,'h\n\n\x01\x10',1,0)

>>> scanner_init.tokenize(scanner, '(hi(mom ()))')
LexToken(LP_TOK,'(',1,0)
LexToken(NAME,'hi',1,1)
LexToken((,'(',1,3)
LexToken(NAME,'mom',1,4)
LexToken(LP_TOK,'(',1,8)
LexToken(),')',1,9)
LexToken(),')',1,10)
LexToken(),')',1,11)

>>> scanner_init.tokenize(scanner, '[hi[mom []]]')
LexToken(LB_TOK,'[',1,0)
LexToken(NAME,'hi',1,1)
LexToken([,'[',1,3)
LexToken(NAME,'mom',1,4)
LexToken(LB_TOK,'[',1,8)
LexToken(],']',1,9)
LexToken(],']',1,10)
LexToken(],']',1,11)

>>> scanner_init.tokenize(scanner, '0 01 10 0x10 0X10 1/2 2.3/4 2.54/ .54/')
LexToken(INTEGER,0,1,0)
LexToken(INTEGER,1,1,2)
LexToken(INTEGER,10,1,5)
LexToken(INTEGER,16,1,8)
LexToken(INTEGER,16,1,13)
LexToken(RATIO,(1, 2),1,18)
LexToken(RATIO,(11, 4),1,22)
LexToken(RATIO,(254, 100),1,28)
LexToken(RATIO,(54, 100),1,34)

>>> scanner_init.tokenize(scanner, '0x1/a 0Xc.A/b 0X2.54/ 0x.54/')
LexToken(RATIO,(1, 10),1,0)
LexToken(RATIO,(142, 11),1,6)
LexToken(RATIO,(596, 256),1,14)
LexToken(RATIO,(84, 256),1,22)

>>> scanner_init.tokenize(scanner,
...     '123. 123~1 122~1 123.5 123.5~1 123~1e1 123E1 123~1e-1 123e-1')
LexToken(APPROX_NUMBER,(123, 0),1,0)
LexToken(APPROX_NUMBER,(123, 0),1,5)
LexToken(APPROX_NUMBER,(61, 1),1,11)
LexToken(APPROX_NUMBER,(1976, -4),1,17)
LexToken(APPROX_NUMBER,(988, -3),1,23)
LexToken(APPROX_NUMBER,(77, 4),1,31)
LexToken(APPROX_NUMBER,(308, 2),1,39)
LexToken(APPROX_NUMBER,(197, -4),1,45)
LexToken(APPROX_NUMBER,(197, -4),1,54)

>>> scanner_init.tokenize(scanner,
...     '0x123. 0X123~1 0x122~1 0X123.5 0x123.5~1 0X123~1x1 0x123X1 '
...     '0x123~1x-1 0X123x-1')
LexToken(APPROX_NUMBER,(291, 0),1,0)
LexToken(APPROX_NUMBER,(291, 0),1,7)
LexToken(APPROX_NUMBER,(145, 1),1,15)
LexToken(APPROX_NUMBER,(4661, -4),1,23)
LexToken(APPROX_NUMBER,(4661, -4),1,31)
LexToken(APPROX_NUMBER,(291, 4),1,41)
LexToken(APPROX_NUMBER,(291, 4),1,51)
LexToken(APPROX_NUMBER,(291, -4),1,59)
LexToken(APPROX_NUMBER,(291, -4),1,70)

>>> scanner_init.tokenize(scanner,
...     '0x12-3+ 0X123~1- *22~1 >0X123 >"0x123~1 0X123~1x1\' ')
LexToken(NAME,'0x12-3+',1,0)
LexToken(NAME,'0X123~1-',1,8)
LexToken(NAME,'*22~1',1,17)
LexToken(ARG_LEFT_WORD,'>0X123',1,23)
LexToken(ARG_LEFT_WORD,'>"0x123~1',1,30)
LexToken(NAME,"0X123~1x1'",1,40)

>>> scanner_init.tokenize(scanner, '+ - * -a ~')
LexToken(+,'+',1,0)
LexToken(-,'-',1,2)
LexToken(*,'*',1,4)
LexToken(NEGATE,'negate',1,6)
LexToken(NAME,'a',1,7)
LexToken(NAME,'~',1,9)

>>> token_dict = {'if': 'IF',
...               'else': 'ELSE_TOK',
...               'elif': 'ELIF_TOK',
... }

>>> scanner_init.tokenize(scanner, 'x if bar< elif "hi" else 7', token_dict)
LexToken(NAME,'x',1,0)
LexToken(IF,'if',1,2)
LexToken(ARG_RIGHT_WORD,'bar<',1,5)
LexToken(ELIF_TOK,'elif',1,10)
LexToken(STRING,'hi',1,15)
LexToken(ELSE_TOK,'else',1,20)
LexToken(INTEGER,7,1,25)

