#!/usr/bin/python

# ide.py

r'''Package editing GUI for uCC project.

Prototype:

ide.py [packagePath]
'''

if __name__ == '__main__':
    from doctest_tools import setpath
    setpath.setpath(__file__, remove_first = True)
    from ucc.gui.App import App

    App().MainLoop()
