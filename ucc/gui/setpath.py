# setpath.py

import sys
import os.path

path, last = os.path.split(__file__)
while last and last.lower() != 'ucc':
    path, last = os.path.split(path)
assert last, "'ucc' directory not found on %r" % __file__

if sys.path[0].startswith(os.path.join(path, '')):
    sys.path[0] = path
elif sys.path[0] == '':
    sys.path.insert(1, path)
else:
    sys.path.insert(0, path)
#print "sys.path:", sys.path
