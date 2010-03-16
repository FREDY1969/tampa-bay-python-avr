#!/usr/local/bin/python3.1

# ide.py

r'''Package editing GUI for uCC project.

Prototype:

ide.py [packagePath]
'''

import sys
from doctest_tools import setpath
setpath.setpath(__file__, remove_first = True)
from ucc.gui.app import App

if __name__ == '__main__':
    try: packagePath = sys.argv[1]
    except IndexError: packagePath = None
    
    App(packagePath).MainLoop()
