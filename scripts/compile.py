#!/usr/bin/python

# compile.py package_dir

import os
import sys

from doctest_tools import setpath
setpath.setpath(__file__, remove_first = True)

from ucc.parser import compile
from ucc.word import top_package

def usage():
    sys.stderr.write("usage: %s package_dir\n" % os.path.basename(sys.argv[0]))
    sys.exit(2)

if __name__ == '__main__':
    if len(sys.argv) != 2: usage()
    compile.run(top_package.top(sys.argv[1]))

