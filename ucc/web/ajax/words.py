# words.py

"""Handle requests for words."""

import os

from ucc.word import top_package

def get(session, data):
    """Return a jsTree compatible tree of words for the package."""

    def buildSerializedTree(words, parent=None):
        """Recurse over the package and return a list tree of words."""
        # setup children list to append serialized words to
        if parent is None:
            children = parent = []
        else:
            try:
                children = parent['children']
            except KeyError:
                children = parent['children'] = [];

        # serialize words
        for word in words:
            serialized = {
                'name': word.name,
                # 'label': word.label,
                'data': word.label,
                'state': 'open' if parent is children else None
            }
            children.append(serialized);
            buildSerializedTree(word.subclasses, serialized)
            buildSerializedTree(word.instances, serialized)

        # remove empty children list
        if parent is not children and len(parent['children']) == 0:
            del parent['children']

        return parent

    top = top_package.top(os.path.abspath('examples/gui_test'))
    serializedTree = buildSerializedTree(top.roots);

    return '200 OK', [], serializedTree
