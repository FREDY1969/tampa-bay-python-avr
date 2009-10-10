# setpath.py

import sys
import os.path

def package_dir(dirname):
    return any(map(lambda suffix:
                     os.path.exists(os.path.join(dirname,
                                                 '__init__.' + suffix)),
                   ('py', 'pyc', 'pyo')))

def setpath(filename, nochange = False):
    dirname, basename = os.path.split(os.path.abspath(filename))
    #print "dirname", dirname
    while basename and package_dir(dirname):
        dirname, basename = os.path.split(dirname)
        #print "dirname", dirname
    assert basename, "non-package directory not found for %r" % __file__

    if dirname in sys.path:
        newpath = sys.path
    elif sys.path[0].startswith(os.path.join(dirname, '')) or sys.path[0] == '':
        newpath = [dirname] + sys.path[1:]
    else:
        newpath = [dirname] + sys.path
    if nochange:
        print "sys.path:", newpath
    else:
        sys.path = newpath
    return dirname
