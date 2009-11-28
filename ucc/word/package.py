# package.py

import os
from doctest_tools import setpath
from ucc.word import helpers, xml_access, word

Built_in = 'ucclib.built_in'

class package(object):
    r'''Object representing a single package.

    Creating the object adds the proper path info to sys.path for the compiler
    to be able to import the Python modules in the package.

    After creating the object, it has these attributes:

        package_dir      - the abspath of the package directory
        package_name     - a standard Python dotted package name that can be
                           imported (e.g., 'examples.blinky')

    Use the 'built_in' class for the ucclib.built_in package.
    '''

    def __init__(self, package_dir):
        # Figure out package directories.
        self.package_dir = os.path.abspath(package_dir)
        root_dir = setpath.setpath(self.package_dir, False)
        assert self.package_dir.startswith(root_dir), \
               "compile.py: setpath did not return a root of package_dir,\n" \
               "  got %s\n" \
               "  for %s" % (root_dir, self.package_dir)
        self.package_name = self.package_dir[len(root_dir) + 1:] \
                                .replace(os.sep, '.') \
                                .replace('/', '.')
        self.load_words()

    def load_words(self):
        self.word_dict = dict((name, self.read_word(name))
                              for name
                               in xml_access.read_word_list(self.package_dir)[1]
                             )

    def get_words(self):
        return self.word_dict.values()

    def read_word(self, name):
        ans = word.read_word(name, self.package_dir)
        ans.package_name = self.package_name
        return ans

class built_in(package):
    def __init__(self):
        self.package_name = Built_in
        self.package_dir = \
          os.path.split(helpers.import_module(self.package_name).__file__)[0]
        self.load_words()

