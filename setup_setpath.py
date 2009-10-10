#!/usr/bin/env python

from distutils.core import setup

setup(
    name = "setpath",
    version = "0.1",
    py_modules = ['setpath'],

    # Metadata for upload to PyPI
    author = "Bruce Frederiksen",
    author_email = "dangyogi@gmail.com",
    description = "Set sys.path to the first parent directory without an __init__.py file",
    long_description = """
        To use:

        >>> import setpath
        >>> setpath.setpath(__file__)
    """,
)
