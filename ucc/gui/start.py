#!/usr/bin/env python

# start.py

r'''Package editing GUI for uCC project.

Prototype:

start.py [packagePath]'''

if __name__ == '__main__':
    from doctest_tools import setpath
    setpath.setpath(__file__, remove_first = True)
    from ucc.gui.App import App
    
    App().MainLoop()
