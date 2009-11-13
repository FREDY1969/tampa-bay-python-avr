# operator.py

from ucclib.built_in import declaration

class operator(declaration.word):
    r'''Used for operators that go straight into intermediate code.
    
    The label is used as the intermediate code operator.
    ''' 
    def compile_generic(self, ast_node, words_by_label):
        print "implement operator.compile_generic"

