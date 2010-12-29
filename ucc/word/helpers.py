# helpers.py

import sys   # only for debugging
import re

Reserved_words = frozenset((
    #: Python's reserved word list (for python 2.6).
    'and', 'del', 'from', 'not', 'while',
    'as', 'elif', 'global', 'or', 'with',
    'assert', 'else', 'if', 'pass', 'yield',
    'break', 'except', 'import', 'print',
    'class', 'exec', 'in', 'raise',
    'continue', 'finally', 'is', 'return',
    'def', 'for', 'lambda', 'try',
))

Illegal_identifier = re.compile(r'[^a-zA-Z0-9_]')

def legalize_name(name):
    name = Illegal_identifier.sub('_', name)
    if name in Reserved_words: name += '_'
    return name

def import_module(modulename):
    ''' ``modulename`` is full package path (with dots).'''
    #print("import_module", repr(modulename), file=sys.stderr)
    #print("sys.path", sys.path, file=sys.stderr)
    #import examples
    #print("examples.__file__", examples.__file__, file=sys.stderr)
    mod = __import__(modulename)
    for comp in modulename.split('.')[1:]:
        mod = getattr(mod, comp)
    return mod
    
