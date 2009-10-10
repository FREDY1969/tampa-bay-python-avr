#!/usr/bin/env python

'''Package editing GUI for uCC project.

Prototype:

start.py [packagePath]'''

if __name__ == '__main__':
    import setpath
    setpath.setpath(__file__)
    from ucc.gui.App import App
    
    App().MainLoop()