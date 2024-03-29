# compile.py

import os
import time

from ucc.compiler import parse, optimize
from ucc.assembler import assemble
from ucc.codegen import codegen
from ucc.database import crud, block, symbol_table, ucl_types

Debug = 0

def run(top, processor, prime_start_time = True, quiet = False):
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
        if not quiet: print("top: {:.2f}".format(elapsed()))

    with crud.db_connection(top.packages[-1].package_dir, True, True, True) \
      as db_conn:
        db_conn.attach(os.path.join(os.path.dirname(codegen.__file__),
                                    'avr.db'),
                       'architecture')

        if not quiet: print("crud.db_connection: {:.2f}".format(elapsed()))

        symbol_table.init()
        ucl_types.init()
        block.init()
        if not quiet: print("*.init: {:.2f}".format(elapsed()))

        # Load word_objs, create symbols, and build the parsers for each
        # package:
        #
        # {package_name: parser module}
        package_parsers = parse.create_parsers(top)
        if not quiet: print("create parsers: {:.2f}".format(elapsed()))

        # word files => ast
        words_done = parse.parse_needed_words(top, package_parsers, quiet)
        if not quiet: print("parse_needed_words: {:.2f}".format(elapsed()))

        # ast => intermediate code
        for word_label in words_done:
            with db_conn.db_transaction():
                symbol_table.get(word_label).word_obj.compile()
        if not quiet:
            print("generate intermediate code: {:.2f}".format(elapsed()))

        # intermediate code => optimized intermediate code
        optimize.optimize()
        if not quiet: print("optimize: {:.2f}".format(elapsed()))

        # intermediate code => assembler
        codegen.gen_assembler(processor)
        if not quiet: print("gen_assembler: {:.2f}".format(elapsed()))

        # assembler => .hex files
        assemble.assemble_program(top.packages[-1].package_dir)
        if not quiet: print("assemble_program: {:.2f}".format(elapsed()))
    if not quiet: print("TOTAL: {:.2f}".format(Start_time - compile_start_time))

Start_time = 0.0

def elapsed():
    global Start_time
    end_time = time.time()
    ans = end_time - Start_time
    Start_time = end_time
    return ans
