# package.py

import sys   # only for debugging
import os
from doctest_tools import setpath
from ucc.word import helpers, xml_access, word

BUILT_IN = 'ucclib.built_in'

class package:
    r'''Object representing a single package.
    
    Creating the object adds the proper path info to sys.path for the compiler
    to be able to import the Python modules in the package.
    
    After creating the object, it has these attributes:
    
        package_dir
          the abspath of the package directory
        package_name
          a standard Python dotted package name that can be imported
          (e.g., 'examples.blinky')
    
    Use the `built_in` class for the `ucclib.built_in` package.
    
    '''
    
    def __init__(self, top_package, package_dir):
        # Figure out package directories.
        self.package_dir = os.path.abspath(package_dir)
        root_dir = setpath.setpath(self.package_dir, False)[0]
        print("package: root_dir", root_dir, file=sys.stderr)
        assert self.package_dir.startswith(root_dir), \
               "{}: setpath did not return a root of package_dir,\n" \
               "  got {}\n" \
               "  for {}".format(os.path.basename(__file__), 
                                 root_dir, 
                                 self.package_dir)
        self.package_name = self.package_dir[len(root_dir) + 1:] \
                                .replace(os.sep, '.') \
                                .replace('/', '.')
        self.package_label = self.load_words(top_package)
        print("package: package_name", self.package_name, file=sys.stderr)
        print("package: package_label", self.package_label, file=sys.stderr)

    def load_words(self, top_package):
        package_label, words = xml_access.read_word_list(self.package_dir)
        self.word_dict = {name: self.read_word(name, top_package)
                          for name in words}
        return package_label

    def get_words(self):
        return list(self.word_dict.values())
    
    def read_word(self, name, top_package):
        return word.read_word(name, self, top_package)


class built_in(package):
    r'''Represents the `ucclib.built_in` package.
    
    The built_in package is automatically available to all other packages.
    '''
    def __init__(self, top_package):
        self.package_name = BUILT_IN
        self.package_dir = \
          os.path.split(helpers.import_module(self.package_name).__file__)[0]
        self.package_label = self.load_words(top_package)

