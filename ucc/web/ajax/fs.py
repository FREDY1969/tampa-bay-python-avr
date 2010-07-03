# fs.py

"""Pull information from the filesystem for the GUI."""

import os

def examples(session, data):
    """Pull in the example packages."""
    return '200 OK', [], os.listdir(os.path.abspath('examples'))
