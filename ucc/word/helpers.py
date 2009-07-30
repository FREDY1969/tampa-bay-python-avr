# helpers.py

import re

# Python's reserved word list (for python 2.6).
Reserved_words = set((
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

def import_module(project_pkg, modulename):
    ''' project_pkg is full package path (with dots).
    '''
    mod = __import__(project_pkg + '.' + modulename)
    for comp in project_pkg.split('.')[1:]:
        mod = getattr(mod, comp)
    return getattr(mod, modulename)

