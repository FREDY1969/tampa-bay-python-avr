# Introduction #

Please follow the following directions to fix the
dreaded crlf incompatibilities with unix (see below) and windows.


# Details #

Reference:
http://mercurial.selenic.com/wiki/Win32TextExtension

This really is very simple.
Go to your user directory found in:
`C:\Documents and Settings\yourname`

In this directory is the following file: `mercurial.ini`

Copy and paste the following lines.  These lines should go right after your `username`
(in the `[ui]` section).

```
[extensions]

fetch = 

hgext.win32text = 


[encode]  

**.py = dumbencode:

**.tst = dumbencode:

**.asm = dumbencode:

**.xml = dumbencode:

**.ucl = dumbencode:

**.ddl = dumbencode:

**.sql = dumbencode:

*SYNTAX = dumbencode:


[decode] 

**.py = dumbdecode:

**.tst = dumbdecode:

**.asm = dumbdecode:

**.xml = dumbdecode:

**.ucl = dumbdecode:

**.ddl = dumbdecode:

**.sql = dumbdecode:

*SYNTAX = dumbdecode:


[patch]

eol = crlf
```

That is it!

Good luck. If you have trouble reference the url above.

bc


**Yes I said it, linux is unix despite
popular belief. If it tastes like a duck, smells like a duck, feels like a duck
it is a duck.**