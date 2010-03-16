# parse.py

import sys
import os.path
import traceback

from ucc.word import helpers
from ucc.parser import genparser
from ucc.database import crud, fn_xref, symbol_table
from ucclib.built_in import declaration

Debug = 0

def load_word(ww):
    r'''Loads and returns the word_obj for ww.
    
    Also creates symbol_table entries and updates Rules and Token_dict.
    '''
    global Rules, Token_dict
    if not hasattr(ww, 'symbol') or ww.symbol is None:
        ww.symbol = \
          symbol_table.symbol.create(ww.label, ww.kind,
                                     source_filename=ww.get_filename())
        ww.symbol.word_word = ww
    if ww.symbol.word_obj is None:
        if not ww.is_root():
            load_word(ww.kind_obj)

        # load new_word
        if ww.is_root():
            assert ww.defining, \
                   "%s: root word that is not a defining word" % ww.label
            new_word = declaration.load_class(ww)
            new_syntax = None
        elif ww.defining:
            new_word, new_syntax = \
              ww.kind_obj.symbol.word_obj.create_subclass(ww)
        else:
            new_word, new_syntax = \
              ww.kind_obj.symbol.word_obj.create_instance(ww)

        # store new_syntax
        if new_syntax:
            r, td = new_syntax
            Rules.extend(r)
            Token_dict.update(td)

        # Add new word to ww.symbol
        ww.symbol.word_obj = new_word
        return new_word
    return ww.symbol.word_obj

def create_parsers(top):
    r'''Creates a parser in each package.

    Returns {package_name: parser module}

    Also does load_word on all of the defining words.
    '''
    global Rules, Token_dict

    Rules = []
    Token_dict = {}
    package_parsers = {}

    syntax_file = os.path.join(os.path.dirname(genparser.__file__), 'SYNTAX')
    with crud.db_transaction():
        for p in top.packages:
            for ww in p.get_words():
                load_word(ww)

            #print "Rules", Rules
            #print "Token_dict", Token_dict

            # compile new parser for this package:
            with open(os.path.join(p.package_dir, 'parser.py'), 'w') \
              as output_file:
                genparser.genparser(syntax_file, '\n'.join(Rules), Token_dict,
                                    output_file)

            # import needed modules from the package:
            package_parsers[p.package_name] = \
              helpers.import_module(p.package_name + '.parser')
    return package_parsers

def parse_word(ww, word_obj, parser):
    r'''Parses the word with the parser.

    Return (True, frozenset(word labels needed)) on success,
           (False, None) on failure.

    Catches exceptions and prints its own error messages.

    This needs an crud.db_connection open.
    '''
    try:
        if not isinstance(word_obj, type): # word_obj not a class
            needs = word_obj.parse_file(parser, Debug)
    except SyntaxError:
        e_type, e_value, e_tb = sys.exc_info()
        for line in traceback.format_exception_only(e_type, e_value):
            sys.stderr.write(line)
        return False, None
    except Exception:
        traceback.print_exc()
        return False, None
    return True, needs

def parse_needed_words(top, package_parsers, quiet):
    r'''Parses all of the needed word files.

    Returns a set of the labels of the words parsed.
    '''
    words_done = set()
    words_needed = set(['startup'])
    num_errors = 0
    while words_needed:
        next_word = words_needed.pop()
        ww = top.get_word_by_label(next_word)
        word_obj = ww.symbol.word_obj
        status, more_words_needed = \
          parse_word(ww, word_obj, package_parsers[ww.package_name])
        if status:
            words_done.add(next_word)
            words_needed.update(more_words_needed - words_done)
        else:
            num_errors += 1

    if num_errors:
        sys.stderr.write("%s files had syntax errors\n" % num_errors)
        sys.exit(1)

    with crud.db_transaction():
        fn_xref.expand(quiet)
    return words_done

