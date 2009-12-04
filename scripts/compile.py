#!/usr/bin/python

# compile.py package_dir

import os
import sys

from doctest_tools import setpath
setpath.setpath(__file__, remove_first = True)

from ucc.parser import compile
from ucc.word import top_package

def usage():
    sys.stderr.write("usage: %s [-d] package_dir\n" %
                       os.path.basename(sys.argv[0]))
    sys.exit(2)

if __name__ == '__main__':
    if len(sys.argv) < 2: usage()
    if sys.argv[1] == '-d':
        compile.Debug = 1
        del sys.argv[1]
    if len(sys.argv) != 2: usage()
    compile.elapsed()
    top = top_package.top(sys.argv[1])
    compile.run(top, False)

