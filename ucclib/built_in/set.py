# set.py

from ucclib.built_in import singleton

class set(singleton.singleton):
    def update_expect(self, ast_node):
        ast_node.args[1][0].expect = 'lvalue'

