# print_r.py

import pprint
import sys

def print_r(obj, stream = sys.stdout, indent = 2, width = 80, depth = 10):
    if not hasattr(obj, '__dict__'):
        pprint.pprint(obj, stream, indent, width, depth)
    else:
        print >> stream, "%s%s:" % (' ' * indent, obj.__class__.__name__)
        indent += 2
        for attr in sorted(obj.__dict__.keys()):
            print >> stream, "%s%s = " % (' ' * indent, attr),
            print_r(getattr(obj, attr), stream, indent + 2, width, depth)
