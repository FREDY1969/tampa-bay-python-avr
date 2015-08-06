(See the 'if' word in examples/washer).

# Lexical #

  1. Tokens (terminals) are either a single character in single quotes, e.g. 'x', or all uppercase.
  1. Single character tokens and tokens ending with `_TOK` are not counted as an argument.  (Exception if a single character token has a parameter list).
  1. Nonterminals are all lowercase.
  1. The names of nonterminals that result in tuples are enclosed in [ ].
  1. Comments are # to end of line.
  1. Lines that are not indented start a new nonterminal definition.
  1. Indenting level otherwise doesn't matter.
  1. Triple quotes are not allowed in python code.
  1. Commas and closing parenthesis (')') are not allowed in python code outside of quoted strings.
  1. Comments are not allowed in python code.


# Syntax #

```
    file :
         | file NEWLINE_TOK
         | file rule NEWLINE_TOK

    rule : NONTERMINAL param_list_opt ':' alternatives
         | TUPLE_NONTERMINAL ':' alternatives

    alternatives : production
                 | alternatives '|' production

    production:
              | production word

    word: parameterized_word
        | sub_rule '?'
        | sub_rule '+'
        | sub_rule '*'
        | sub_rule ELLIPSIS

    parameterized_word: sub_rule
                      | simple_word param_list

    sub_rule: simple_word
            | simple_word AS_TOK NONTERMINAL
            | '(' alternatives ')'

    simple_word: TOKEN_IGNORE
               | CHAR_TOKEN
               | TOKEN
               | NONTERMINAL
               | TUPLE_NONTERMINAL

    param_list_opt:
                  | param_list

    param_list : START_PARAMS parameters_opt ')'

    parameters_opt:
                  | parameters

    parameters: parameter
              | parameters ',' parameter

    parameter: NONTERMINAL PYTHON_CODE

```