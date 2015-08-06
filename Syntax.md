# Lexical #

Tabs are not allowed anywhere in the file (including within comments or string literals).

Comments start with '#' and go to the end of the line (like Python).

Character literals are enclosed in ', and string literals are enclosed in ".  Both may contain \a, \b, \f, \n, \r, \t, \v or \xXX escapes (where X is a hex digit).  Additionally, the \ escapes any other character.

A character literal is treated as an 8 bit unsigned integer literal.

Words are delimited differently than most other languages.  This takes the importance of whitespace to the next level (from what Python does).  SO PAY ATTENTION!

Words are identified as follows:

  1. The following characters are not allowed in words: `[(.<sp>\r\n`
  1. In addition, the word may not start with: `-"'#`
  1. Or end with: `]):`

Or as the single character: .

Thus, the following are legal words:

  * )+
  * foo-bar
  * a-
  * f2\_bar
  * 3x
  * 123
  * .

And this text:

```
   I.wonder-how(this+4)gets[chopped +into]words#or not!
```

Is taken as the following sequence of tokens:

| **Token**        | **Interpretation** |
|:-----------------|:-------------------|
| I                | a word             |
| .                | a word             |
| wonder-how       | a word             |
| (                | special punctuation, not a word |
| this+4)gets      | a word             |
| [                | special punctuation, not a word |
| chopped          | a word             |
| +into]words#or   | a word -- specifically, does **not** contain a comment! |
| not!             | a word             |

While this text:

```
   I .wonder -how(this +4) gets[chopped + into] words #or not!
```

Is taken as:

| **Token**        | **Interpretation** |
|:-----------------|:-------------------|
| I                | a word             |
| .                | a word             |
| wonder           | a word             |
| -                | special punctuation -- taken as unary negate, **not** binary minus (because of the lack of whitespace following the -) |
| how              | a word             |
| (                | special punctuation, not a word |
| this             | a word             |
| +4               | a word, not an integer |
| )                | special punctuation, not a word |
| gets             | a word             |
| [                | special punctuation, not a word |
| chopped          | a word             |
| +                | special punctuation, not a word |
| into             | a word             |
| ]                | special punctuation, not a word |
| words            | a word -- followed by a comment |

Then, if the word looks like a number, it is treated as a numeric literal.  Thus **4+** is ok as a word (but is not taken as a numeric literal).

There are three kinds of numeric literals.  A preceding - is taken as a separate token (though you probably wouldn't notice this).  Here `digits` means one or more decimal digit, `hexits` means one or more hex digits, `[xxx]` means optional xxx.

  1. integer literals (These are taken as exact numbers.)
    * `digits`
      * 123
    * `0xhexits`
      * 0x123
      * 0xabc
      * 0xABC
      * 0X123
  1. ratio literals (These are taken as exact numbers and always include a / character.)
    * `digits[.digits]/digits`
      * 3/4
      * 1.3/4 (means "1 and 3/4", or 7/4)
    * `[digits].digits/`
      * 2.54/ (denominator assumed, same as 2.54/100)
      * .54/ (denominator assumed, same as 54/100)
    * These may also be preceded by 0x for a hex form (both numerator and denominator in hex).
  1. approximate numbers (These are taken as approximate numbers, where the accuracy is indicated by the number of digits after the decimal point.  These are indicated by . e or ~ without a /.)
    * `digits.[digits][~digit][e[+-]digits]`
      * 44. (accurate to within +/-0.5, vs 44 which is exact)
      * 44.0 (accurate to within +/-0.05)
      * 44.0~2 (accurate to within +/-0.2)
      * 4.4e2 (accurate to within +/-5)
    * `.digits[~digit][e[+-]digits]`
      * .4 (accurate to within +/-0.05)
      * .4~2 (accurate to within +/-0.2)
      * .4e2 (accurate to within +/-5)
    * `digits[~digit]e[+-]digits`
      * 4e2 (accurate to within +/-50)
      * 44~2e2 (accurate to within +/-200)
    * `digits~digit`
      * 44~2 (accurate to within +/-2)
    * These may also be preceded by 0x for a hex form (all digits but the exponent in hex).

## Line continuations ##

Lines ending in : introduce a series of subordinate statements (like Python).  The subordinate statements must be indented exactly 4 spaces (unlike Python).

If a line doesn't end in : and the following line is indented (any amount, not restricted to 4 spaces), it is taken as a line continuation.  Thus, the \ at the end of the line is not required (as it is in Python).

# Syntax #

Here `xxx*` means zero or more `xxx`, `xxx+` means one or more `xxx`, and `[xxx]` means optional `xxx`.  Tokens are all uppercase.

NOTE: all binary operators must be preceded and followed by whitespace.

Note that the arguments to functions are not separated by commas.

There is one statement per line:

```
file : statement+

statement : simple_statement
          | NAME expr* series

simple_statement : NAME expr* NEWLINE

series : ':' simple_statement
       | ':' NEWLINE INDENT statement+ DEINDENT

lvalue: NAME
      | expr '[' expr* ']'  # NOTE: '[' must NOT be preceded by whitespace!
      | expr '.' NAME

expr : APPROX_NUMBER
     | CHAR
     | INTEGER
     | RATIO
     | STRING
     | lvalue
     | '(' expr ')'        # NOTE: '(' must be preceded by whitespace!
     | expr '(' expr* ')'  # NOTE: '(' must NOT be preceded by whitespace!
     | 'bit_not' expr
     | '-' expr            # NOTE: '-' must NOT be followed by whitespace!
     | expr 'bit_and' expr
     | expr 'bit_xor' expr
     | expr 'bit_or' expr
     | expr '*' expr
     | expr '/' expr
     | expr '%' expr
     | expr '+' expr
     | expr '-' expr       # NOTE: '-' must be followed by whitespace!
     | NAME< expr          # NOTE: NAME ends with <
     | expr >NAME          # NOTE: NAME starts with >
     | expr '<' expr
     | expr '<=' expr
     | expr '=' expr       # NOTE: '=' for "equal", not '=='!
     | expr '!=' expr
     | expr '>' expr
     | expr '>=' expr
     | 'not' expr
     | expr 'and' expr
     | expr 'or' expr
```

The control statements (if, while, etc) are user-defined as macros (see MetaSyntax).

You'll see that there are five forms for calling a function:

  1. As a statement, where the first word on the line is the function and everything else on the same line are its arguments.
    * Examples:
      * motor on
      * digitalWrite pin value
  1. As an expression by enclosing the arguments in ( ) after the function word (with no intervening whitespace).
    * Examples:
      * max(a b)
  1. As an expression when the function name ends with <, it takes a single argument that follows the function (with no ( ) required).
    * Examples:
      * to-string< value
  1. As an expression when the function name starts with >, it takes a single argument that precedes the function (with no ( ) required).
    * Examples:
      * value >to-pwm
  1. As an expression taking no arguments when none of the above apply.
    * Examples:
      * check-button