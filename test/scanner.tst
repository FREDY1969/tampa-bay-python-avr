# scanner.tst

>>> from ucc.parser import scanner

>>> scanner.tokenize(scanner, {}, 'hi mom')
LexToken(NAME_TOK,'hi',1,0)
LexToken(NAME_TOK,'mom',1,3)

>>> scanner.tokenize(scanner, {}, 'hi\n mom')
LexToken(NAME_TOK,'hi',1,0)
LexToken(NAME_TOK,'mom',2,4)

>>> scanner.tokenize(scanner, {}, 'hi\n  mom\n dad')
LexToken(NAME_TOK,'hi',1,0)
LexToken(NAME_TOK,'mom',2,5)
LexToken(NAME_TOK,'dad',3,10)

>>> scanner.tokenize(scanner, {}, 'hi:\n    mom\ndad')
LexToken(NAME_TOK,'hi',1,0)
LexToken(START_SERIES_TOK,':\n',1,2)
LexToken(INDENT_TOK,'\n    ',2,3)
LexToken(NAME_TOK,'mom',2,8)
LexToken(NEWLINE_TOK,'\n',2,11)
LexToken(DEINDENT_TOK,'\n',3,11)
LexToken(NAME_TOK,'dad',3,12)

>>> scanner.tokenize(scanner, {}, r"'h' '\n' '\N' '\x01' '\X10'")
LexToken(CHAR_TOK,104,1,0)
LexToken(CHAR_TOK,10,1,4)
LexToken(CHAR_TOK,10,1,9)
LexToken(CHAR_TOK,1,1,14)
LexToken(CHAR_TOK,16,1,21)

>>> scanner.tokenize(scanner, {}, r'"h\n\N\x01\X10"')
LexToken(STRING_TOK,'h\n\n\x01\x10',1,0)

>>> scanner.tokenize(scanner, {}, '(hi(mom ()))')
LexToken(LP_TOK,'(',1,0)
LexToken(NAME_TOK,'hi',1,1)
LexToken((,'(',1,3)
LexToken(NAME_TOK,'mom',1,4)
LexToken(LP_TOK,'(',1,8)
LexToken(),')',1,9)
LexToken(),')',1,10)
LexToken(),')',1,11)

>>> scanner.tokenize(scanner, {}, '[hi[mom []]]')
LexToken(LB_TOK,'[',1,0)
LexToken(NAME_TOK,'hi',1,1)
LexToken([,'[',1,3)
LexToken(NAME_TOK,'mom',1,4)
LexToken(LB_TOK,'[',1,8)
LexToken(],']',1,9)
LexToken(],']',1,10)
LexToken(],']',1,11)

>>> scanner.tokenize(scanner, {}, '0 01 10 0x10 0X10 1/2 2.3/4 2.54/ .54/')
LexToken(INTEGER_TOK,0,1,0)
LexToken(INTEGER_TOK,1,1,2)
LexToken(INTEGER_TOK,10,1,5)
LexToken(INTEGER_TOK,16,1,8)
LexToken(INTEGER_TOK,16,1,13)
LexToken(RATIO_TOK,(1, 2),1,18)
LexToken(RATIO_TOK,(11, 4),1,22)
LexToken(RATIO_TOK,(254, 100),1,28)
LexToken(RATIO_TOK,(54, 100),1,34)

>>> scanner.tokenize(scanner, {}, '0x1/a 0Xc.A/b 0X2.54/ 0x.54/')
LexToken(RATIO_TOK,(1, 10),1,0)
LexToken(RATIO_TOK,(142, 11),1,6)
LexToken(RATIO_TOK,(596, 256),1,14)
LexToken(RATIO_TOK,(84, 256),1,22)

>>> scanner.tokenize(scanner, {},
...     '123. 123~1 122~1 123.5 123.5~1 123~1e1 123E1 123~1e-1 123e-1')
LexToken(APPROX_NUMBER_TOK,(123, 0),1,0)
LexToken(APPROX_NUMBER_TOK,(123, 0),1,5)
LexToken(APPROX_NUMBER_TOK,(61, 1),1,11)
LexToken(APPROX_NUMBER_TOK,(1976, -4),1,17)
LexToken(APPROX_NUMBER_TOK,(988, -3),1,23)
LexToken(APPROX_NUMBER_TOK,(77, 4),1,31)
LexToken(APPROX_NUMBER_TOK,(308, 2),1,39)
LexToken(APPROX_NUMBER_TOK,(197, -4),1,45)
LexToken(APPROX_NUMBER_TOK,(197, -4),1,54)

>>> scanner.tokenize(scanner, {},
...     '0x123. 0X123~1 0x122~1 0X123.5 0x123.5~1 0X123~1x1 0x123X1 '
...     '0x123~1x-1 0X123x-1')
LexToken(APPROX_NUMBER_TOK,(291, 0),1,0)
LexToken(APPROX_NUMBER_TOK,(291, 0),1,7)
LexToken(APPROX_NUMBER_TOK,(145, 1),1,15)
LexToken(APPROX_NUMBER_TOK,(4661, -4),1,23)
LexToken(APPROX_NUMBER_TOK,(4661, -4),1,31)
LexToken(APPROX_NUMBER_TOK,(291, 4),1,41)
LexToken(APPROX_NUMBER_TOK,(291, 4),1,51)
LexToken(APPROX_NUMBER_TOK,(291, -4),1,59)
LexToken(APPROX_NUMBER_TOK,(291, -4),1,70)

>>> scanner.tokenize(scanner, {},
...     '0x12.3. 0X123~1- *22~1 >0X123.5 >"0x123.5~1 0X123~1x1\' ')
LexToken(NAME_TOK,'0x12.3.',1,0)
LexToken(NAME_TOK,'0X123~1-',1,8)
LexToken(NAME_TOK,'*22~1',1,17)
LexToken(NAME_TOK,'>0X123.5',1,23)
LexToken(NAME_TOK,'>"0x123.5~1',1,32)
LexToken(NAME_TOK,"0X123~1x1'",1,44)

>>> scanner.tokenize(scanner, {}, '+ - * -a ~')
LexToken(NAME_TOK,'+',1,0)
LexToken(NAME_TOK,'-',1,2)
LexToken(NAME_TOK,'*',1,4)
LexToken(NAME_TOK,'negate',1,6)
LexToken(NAME_TOK,'a',1,7)
LexToken(NAME_TOK,'~',1,9)

>>> class word(object):
...     def __init__(self, name, token):
...         self.name = name
...         self.token = token
...     def __repr__(self): return "<word %s>" % self.name
>>> word_dict = {'>foo': word('>foo', 'ARG_LEFT_WORD'),
...              'bar<': word('bar<', 'ARG_RIGHT_WORD'),
...              '+': word('+', '+'),
... }

>>> scanner.tokenize(scanner, word_dict, 'x >foo bar< + 7')
LexToken(NAME_TOK,'x',1,0)
LexToken(ARG_LEFT_WORD,<word >foo>,1,2)
LexToken(ARG_RIGHT_WORD,<word bar<>,1,7)
LexToken(+,<word +>,1,12)
LexToken(INTEGER_TOK,7,1,14)

