#!/usr/local/bin/python3.1

# ide-web.py

r'''Web based IDE for uCC project.
'''

from doctest_tools import setpath
setpath.setpath(__file__, remove_first = True)
import ucc.web.server

if __name__ == "__main__":
    ucc.web.server.start()
