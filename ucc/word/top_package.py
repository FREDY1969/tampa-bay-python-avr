# top_package.py

r'''This is the central point of knowledge for a top-level package.

It includes complete word dictionaries that include the words in all of the
packages used by the top package.
'''

from ucc.word import package

class top(object):
    def __init__(self, package_dir = None):
        r'''Omit package_dir to treat built_in as top-level package.
        '''
        self.package_dict = {}
        self.word_dict = {}
        self.translation_dict = {}
        if package_dir is None:
            self.add_package(package.built_in(), True)
        else:
            self.add_package(package.built_in(), False)
            self.add_package(package.package(package_dir), True)
        self.connect_the_dots()

    def add_package(self, package, top):
        for name in package.read_words():
            w = package.read_word(name)
            w.top = top
            if w.label in self.word_dict or w.label in self.translation_dict:
                raise NameError("%s: duplicate label in package %s" %
                                (w.label, package.package_name))
            if w.name in self.word_dict:
                raise NameError("%s: duplicate name in package %s" %
                                (w.name, package.package_name))
            self.word_dict[w.name] = w
            if w.label != w.name:
                self.translation_dict[w.label] = w.name

    def connect_the_dots(self):
        # Link w.kind_obj to the word object (where w.kind is just the name).
        # Add w.subclasses and w.instances lists and sort these by label.
        # Gather the root words into self.roots and sort this by label.
        for w in self.word_dict.itervalues():
            w.subclasses = []
            w.instances = []
        self.roots = []
        for w in self.word_dict.itervalues():
            w.kind_obj = self.get_word_by_name(w.kind)
            assert w.kind_obj.defining, \
                   "%s: derived from non-defining word %s" % \
                     (w.label, w.kind_obj.label)
            if w.is_root():
                self.roots.append(w)
            else:
                if w.defining: w.kind_obj.subclasses.append(w)
                else: w.kind_obj.instances.append(w)
        self.roots.sort(key=lambda w: w.label)
        for w in self.word_dict.itervalues():
            w.subclasses.sort(key=lambda w: w.label)
            w.instances.sort(key=lambda w: w.label)

    def get_word_by_name(self, name):
        r'''Lookup word by name from all packages.
        '''
        return self.word_dict[name]

    def get_word_by_label(self, label):
        r'''Lookup word by label from all packages.
        '''
        return self.get_name(self.translation_dict.get(label, label))


