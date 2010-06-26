#!/usr/local/bin/python3.1

# ide-web.py

"""Web based IDE for μCC project."""

from doctest_tools import setpath
setpath.setpath(__file__, remove_first = True)

import ucc.web.server
import ucc.web.wsgi_app

def main():
    """Start the server and open a webbrowser."""
    ucc.web.server.start(ucc.web.wsgi_app.wsgi_app)

if __name__ == "__main__":
    main()
