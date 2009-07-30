# ucc.parser.metascanner_tables.py. This file automatically created by PLY (version 3.2). Don't edit!
_tabversion   = '3.2'
_lextokens    = {'CHAR_TOKEN': 1, 'AS_TOK': 1, 'TUPLE_NONTERMINAL': 1, 'PYTHON_CODE': 1, 'TOKEN': 1, 'START_PARAMS': 1, 'ELLIPSIS': 1, 'NEWLINE_TOK': 1, 'TOKEN_IGNORE': 1, 'NONTERMINAL': 1}
_lexreflags   = 64
_lexliterals  = '():|?+*,'
_lexstateinfo = {'python': 'exclusive', 'INITIAL': 'inclusive'}
_lexstatere   = {'python': [('(?P<t_python_escape>\\\\.)|(?P<t_python_quote>[\'"])|(?P<t_python_percent>%)|(?P<t_python_chars>[^\'",)\\\\%]+)|(?P<t_python_PYTHON_CODE>[,)])', [None, ('t_python_escape', 'escape'), ('t_python_quote', 'quote'), ('t_python_percent', 'percent'), ('t_python_chars', 'chars'), ('t_python_PYTHON_CODE', 'PYTHON_CODE')])], 'INITIAL': [("(?P<t_NEWLINE_TOK>(?:\\r)? \\n                          # newline\n        (?: \\ *\n            (?: \\#[^\\t\\r\\n]* )?\n            (?:\\r)? \\n\n          )*                                # any number of blank lines\n        [^#]                                # first character of next line\n    )|(?P<t_NEWLINE_TOK2>(?:\\r)? \\n                          # newline\n        (?: \\ *\n            (?: \\#[^\\t\\r\\n]* )?\n            (?:\\r)? \\n\n          )*                                # any number of blank lines\n    )|(?P<t_AS_TOK>as)|(?P<t_TUPLE_NONTERMINAL>\\[[a-z_][a-z_0-9]*\\]\n    )|(?P<t_TOKEN_IGNORE>[A-Z_][A-Z_0-9]*_TOK)|(?P<t_START_PARAMS>(?<=[]'a-zA-Z_0-9]) \\()|(?P<t_start_python_code>=)|(?P<t_TOKEN>[A-Z_][A-Z_0-9]*)|(?P<t_NONTERMINAL>[a-z_][a-z_0-9]*)|(?P<t_CHAR_TOKEN>'[^\\\\\\t\\r\\n ]')|(?P<t_ignore_comment>\\#[^\\t\\r\\n]*)|(?P<t_ELLIPSIS>\\.\\.\\.)", [None, ('t_NEWLINE_TOK', 'NEWLINE_TOK'), ('t_NEWLINE_TOK2', 'NEWLINE_TOK2'), ('t_AS_TOK', 'AS_TOK'), ('t_TUPLE_NONTERMINAL', 'TUPLE_NONTERMINAL'), ('t_TOKEN_IGNORE', 'TOKEN_IGNORE'), ('t_START_PARAMS', 'START_PARAMS'), ('t_start_python_code', 'start_python_code'), (None, 'TOKEN'), (None, 'NONTERMINAL'), (None, 'CHAR_TOKEN'), (None, None), (None, 'ELLIPSIS')])]}
_lexstateignore = {'python': '', 'INITIAL': ' '}
_lexstateerrorf = {'python': 't_ANY_error', 'INITIAL': 't_ANY_error'}
