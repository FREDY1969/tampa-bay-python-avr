# compile.py

from __future__ import with_statement

import sys
import os.path
import itertools
import traceback
import time

from ucc.word import helpers
from ucc.parser import genparser, hex_file
from ucc.database import crud, fn_xref, symbol_table, types, triple2
from ucc.assembler import assemble
from ucclib.built_in import declaration

Debug = 0

def load_word(ww):
    r'''Loads and returns the word_obj for ww.
    
    And updates Rules and Token_dict.
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

    syntax_file = os.path.join(os.path.dirname(__file__), 'SYNTAX')
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

def optimize():
    pass

def gen_assembler():
    for block_id, name, word_symbol_id, next, next_conditional \
     in crud.read_as_tuples('blocks', 'id', 'name', 'word_symbol_id', 'next',
                                      'next_conditional'):
        triples = triple2.read_triples(block_id)
        if Debug: print >> sys.stderr, "triples", triples
        tops = filter(lambda t: len(t.parents) == 0, triples)
        if Debug: print >> sys.stderr, "tops", tops
        crud.Db_cur.execute('''
            select predecessor, successor
              from triple_order_constraints
             where predecessor in (%(qmarks)s) or successor in (%(qmarks)s)
        ''' % {'qmarks': ', '.join('?' * len(triples))},
        [t.id for t in triples] * 2)
        pred_succ = crud.Db_cur.fetchall()
        if Debug: print >> sys.stderr, "pred_succ", pred_succ
        shareds = filter(lambda s: len(s) > 1,
                         (frozenset(tops(t.parents))
                          for t in triples if len(t.parents) > 1))
        if Debug: print >> sys.stderr, "shareds", shareds
        for top in order_tops(tops, pred_succ, shareds):
            print >> sys.stderr, \
                  'gen_assembler for block', block_id, 'triple', top.id
            #with crud.db_transaction():

def tops(triples):
    return itertools.chain.from_iterable(
             (tops(t.parents) if t.parents else (t,)) for t in triples)

def order_tops(tops, pred_succ, shareds):
    tops = list(tops)
    leftovers = set()

    def process(t_set, shareds):
        def remove(t):
            assert t in tops
            tops.remove(t)
            if t in leftovers: leftovers.remove(t)
            return filter(lambda ps: ps[0] != t and ps[1] != t, shareds)
        for t_shared in pick(t_set, shareds):
            found_one = False
            try_again = True
            while t_shared and try_again:
                try_again = False
                for t in t_shared.copy():
                    if t not in succs:
                        shareds = remove(t)
                        t_shared.remove(t)
                        try_again = True
                        found_one = True
                        yield t, shareds
            assert found_one
            for t in leftovers:
                if t not in succs:
                    shareds = remove(t)
                    yield t, shareds
            leftovers.update(t_shared)
            break
        else:
            assert False, "pick failed"

    while pred_succ:
        if Debug: print >> sys.stderr, "pred_succ", pred_succ
        if Debug: print >> sys.stderr, "tops", tops
        preds = frozenset(ps[0] for ps in pred_succ)
        succs = frozenset(ps[1] for ps in pred_succ)
        available_preds = preds - succs
        assert available_preds
        for t, shareds in process(available_preds, shareds):
            yield t
    if Debug: print >> sys.stderr, "while done: tops", tops
    if tops:
        succs = frozenset(ps[1] for ps in pred_succ)
        for t, shareds in process(frozenset(tops), shareds):
            yield t

def pick(t_set, shareds):
    if Debug: print >> sys.stderr, "pick", t_set, shareds
    t_yielded = set()
    for t in t_set:
        t_shared = set(s for s in shareds if t in s)
        if t_shared:
            t_yielded.add(t)
            yield t_shared
    for t in t_set - t_yielded:
        yield set((t,))

def assemble_program(package_dir):
    r'''Assemble all of the sections.

    Generates .hex files in package_dir.
    '''

    # Assign addresses to all labels in all sections:
    labels = {}         # {label: address}

    with crud.db_transaction():
        # flash
        start_data = assemble.assign_labels('flash', labels)

        # data
        assert 'start_data' not in labels, \
               "duplicate assembler label: start_data"
        labels['start_data'] = start_data
        data_len = assemble.assign_labels('data', labels)
        assert 'data_len' not in labels, \
               "duplicate assembler label: data_len"
        labels['data_len'] = data_len

        # bss
        bss_end = assemble.assign_labels('bss', labels, data_len)
        assert 'bss_len' not in labels, \
               "duplicate assembler label: bss_len"
        labels['bss_len'] = bss_end - data_len

        # eeprom
        assemble.assign_labels('eeprom', labels)

    # assemble flash and data:
    hex_file.write(itertools.chain(assemble.assemble('flash', labels),
                                   assemble.assemble('data', labels)),
                   package_dir, 'flash')

    # check that bss is blank!
    try:
        assemble.assemble('bss', labels).next()
    except StopIteration:
        pass
    else:
        raise AssertionError("bss is not blank!")

    # assemble eeprom:
    hex_file.write(assemble.assemble('eeprom', labels), package_dir, 'eeprom')

def run(top, prime_start_time = True, quiet = False):
    # The following gets a little confusing because we have two kinds of word
    # objects:
    #
    #   1.  ww objects       ("word_word", i.e., instances of the
    #                         ucc.word.word.word class)
    #   2.  word_obj objects (either subclasses or instances of the
    #                         ucclib.built_in.declaration.declaration class)
    #

    if prime_start_time:
        elapsed()       # prime the Start_time...
        compile_start_time = Start_time
    else:
        compile_start_time = Start_time
        if not quiet: print "top: %.2f" % elapsed()

    with crud.db_connection(top.packages[-1].package_dir):
        if not quiet: print "crud.db_connection: %.2f" % elapsed()

        types.init()
        if not quiet: print "types.init: %.2f" % elapsed()

        # Create symbols, word_objs and build the parsers for each package:
        #
        # {package_name: parser module}
        package_parsers = create_parsers(top)  # Also loads all of the word objs
        if not quiet: print "create parsers: %.2f" % elapsed()

        # word files => ast
        words_done = parse_needed_words(top, package_parsers, quiet)
        if not quiet: print "parse_needed_words: %.2f" % elapsed()

        # ast => intermediate code
        for word_label in words_done:
            with crud.db_transaction():
                symbol_table.get(word_label).word_obj.compile()
        if not quiet: print "generate intermediate code: %.2f" % elapsed()

        # intermediate code => optimized intermediate code
        optimize()
        if not quiet: print "optimize: %.2f" % elapsed()

        # intermediate code => assembler
        gen_assembler()
        if not quiet: print "gen_assembler: %.2f" % elapsed()

        # assembler => .hex files
        assemble_program(top.packages[-1].package_dir)
        if not quiet: print "assemble_program: %.2f" % elapsed()
    if not quiet: print "TOTAL: %.2f" % (Start_time - compile_start_time)

Start_time = 0.0

def elapsed():
    global Start_time
    end_time = time.time()
    ans = end_time - Start_time
    Start_time = end_time
    return ans
