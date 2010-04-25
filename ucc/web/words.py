# words.py

'''Handle requests for words.'''

from doctest_tools import setpath
setpath.setpath(__file__, remove_first = True)

import os
from ucc.word import top_package

def get(session, **kwarg):
    def buildSerializedTree(words, parent=[]):
        
        # setup children list to append serialized words to
        
        if type(parent) is dict:
            try: parent['children']
            except KeyError: parent['children'] = [];
            children = parent['children']
        else:
            children = parent
        
        # serialize words
        
        for word in words:
            serialized = {
                'name': word.name,
                # 'label': word.label,
                'data': word.label,
                'state': 'open' if type(parent) is list else None
            }
            children.append(serialized);
            buildSerializedTree(word.subclasses, serialized)
            buildSerializedTree(word.instances, serialized)
        
        # remove empty children list
        
        if type(parent) is dict and parent['children'] == []:
            del(parent['children'])
        
        return parent
    
    top = top_package.top(os.path.abspath('examples/gui_test'))
    serializedTree = buildSerializedTree(top.roots);
    
    return ('200 OK', [], serializedTree)
