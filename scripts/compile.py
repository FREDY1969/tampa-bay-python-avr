#!/usr/local/bin/python3.1

# compile.py package_dir

import os
import sys

from doctest_tools import setpath
setpath.setpath(__file__, remove_first = True)

from ucc.compiler import compile
from ucc.word import top_package

def usage():
    sys.stderr.write("usage: {} [-d] package_dir [processor]\n"
                       .format(os.path.basename(sys.argv[0])))
    sys.exit(2)

def do_compile(args, quiet = False):
    if len(args) < 1: usage()
    if args[0] == '-d':
        compile.Debug = 1
        del args[0]
    if len(args) < 1 or len(args) > 2: usage()
    compile.elapsed()
    top = top_package.top(args[0])
    compile.run(top, 'atmega328p' if len(args) == 1 else args[1], False, quiet)

if __name__ == '__main__':
    do_compile(sys.argv[1:])
