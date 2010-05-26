# code_seq.py

from ucc.database import crud

class code_seq:
    def __init__(self, id):
        self.id = id
        self.parameters = {}    # {param_num: (reg_class, num_registers)}
        self.requirements = {}  # {reg_class: number_of_registers}

    def add_parameter(self, param_num, reg_class, num_registers):
        assert param_num not in self.parameters
        self.parameters[param_num] = (reg_class, num_registers)

    def add_requirement(self, reg_class, num_registers):
        assert reg_class not in self.requirements
        self.requirements[reg_class] = num_registers

def get_code_seq_info():
    r'''Reads code_seq info from machine.db.
    
    Returns {code_seq_id: code_seq object}
    '''
    ans = {}    # {id: code_seq object}
    last_id = None
    for id, param_num, reg_class, num_registers \
     in crud.read_as_tuples('code_seq_parameter', 'code_seq_id',
                            'parameter_num', 'reg_class', 'num_registers'):
        if id != last_id:
            last_id = id
            obj = code_seq(id)
            ans[id] = obj
        obj.add_parameter(param_num, reg_class, num_registers)
    for id, reg_class, num_needed \
     in crud.read_as_tuples('reg_requirements', 'code_seq_id', 'reg_class',
                            'num_needed'):
        ans[id].add_requirement(reg_class, num_needed)
    return ans
