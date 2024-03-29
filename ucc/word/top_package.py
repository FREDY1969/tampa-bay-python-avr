# top_package.py

r'''This is the central point of knowledge for a top-level `package`.

It includes complete word dictionaries that include the words in all of the
packages used by the top package.

'''

from ucc.word import package

class top:
    def __init__(self, package_dir = None):
        r'''Omit package_dir to treat built_in as the top-level package.'''
        self.word_dict = {}
        self.translation_dict = {}
        self.packages = []              # top package last!
        self.packages.append(package.built_in(self))
        if package_dir is not None:
            self.packages.append(package.package(self, package_dir))
        for p in self.packages[:-1]:
            self.add_package(p, False)
        self.add_package(self.packages[-1], True)
        self.connect_the_dots()

    def get_top_package(self):
        return self.packages[-1]

    def add_package(self, package, top):
        r'''Get `package` words and assign them to `word_dict`'''
        for w in package.get_words():
            w.top = top
            if w.label in self.word_dict or w.label in self.translation_dict:
                raise NameError("{}: duplicate label in package {}"
                                  .format(w.label, package.package_name))
            if w.name in self.word_dict:
                raise NameError("{}: duplicate name in package {}"
                                  .format(w.name, package.package_name))
            self.word_dict[w.name] = w
            if w.label != w.name:
                self.translation_dict[w.label] = w.name
    
    def connect_the_dots(self):
        r'''Establish the connections between words. 
        
        - Link w.kind_obj to the word object (where w.kind is just the name).
        - Add w.subclasses and w.instances lists and sort these by label.
        - Gather the root words into self.roots and sort this by label.
        
        '''
        
        for w in self.word_dict.values():
            w.subclasses = []
            w.instances = []
        self.roots = []
        for w in self.word_dict.values():
            w.kind_obj = self.get_word_by_name(w.kind)
            assert w.kind_obj.defining, \
                   "{}: derived from non-defining word {}" \
                     .format(w.label, w.kind_obj.label)
            if w.is_root():
                self.roots.append(w)
            else:
                if w.defining:
                    w.kind_obj.subclasses.append(w)
                else:
                    w.kind_obj.instances.append(w)
        self.roots.sort(key=lambda w: w.label.lower())
        for w in self.word_dict.values():
            w.subclasses.sort(key=lambda w: w.label.lower())
            w.instances.sort(key=lambda w: w.label.lower())
            if w.defining:
                suffix = w.get_value('filename_suffix')
                if suffix and suffix[0] != '.':
                    suffix = '.' + suffix
                w.filename_suffix = suffix

    def get_word(self, name_or_label):
        r'''Lookup `word` by name or label from all packages.'''
        return get_word_by_label(self, name_or_label)
    
    def get_word_by_name(self, name):
        r'''Lookup `word` by name from all packages.'''
        return self.word_dict[name]

    def get_word_by_label(self, label):
        r'''Lookup `word` by label from all packages.'''
        return self.get_word_by_name(self.translation_dict.get(label, label))

    def gen_words(self):
        r'''Generate all of the words in all of the packages.'''
        return self.word_dict.values()

    def gen_top_words(self):
        r'''Generate all of the words in all of the packages.'''
        return self.get_top_package().word_dict.values()

