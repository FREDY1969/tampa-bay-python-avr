# function.py

import itertools

from ucc.database import crud

class function:
    def __init__(self, symbol_id):
        self.id = symbol_id
        self.locals = dict((t[0], make_local(t))
                           for t in crud.read_as_tuples('symbol_table',
                                                        'id', 'label',
                                                        'kind', 'int1',
                                                        context=symbol_id))
        self.collect_calls()
        self.collect_params()

    def collect_calls(self):
        crud.Db_cur.execute('''
            select t.id, tp.id, tp.needed_reg_class, tp.trashed
              from triple_parameters tp
                     inner join triples t
                        on tp.parameter_id = t.id
             where t.kind = 'call_direct'
               and t.symbol_id = ?
             order by t.id
         ''', (self.id,))
        self.calls = tuple(crud.Db_cur.fetchall())

    def collect_params(self):
        # get tuple of unique triple ids (self.calls already sorted on t[0]):
        triple_ids = \
          tuple(k for k, g in itertools.groupby(self.calls, key=lambda t: t[0]))
        crud.Db_cur.execute('''
            select tp.parameter_num, t.reg_class
              from triples t
                     inner join triple_parameters tp
                        on t.id = tp.parent_id
             where t.id in ({})
             order by tp.parameter_num, t.reg_class
         '''.format(', '.join(('?',) * len(triple_ids)),),
         triple_ids)
        # {parameter_num: (reg_class, ...)}
        self.params_provided_reg_classes = \
          dict((parameter_num, tuple(t[1] for t in group))
               for parameter_num, group
                in itertools.groupby(crud.Db_cur.fetchall(),
                                     key = lambda t: t[0]))

def make_local(t):
    id, label, kind, int1 = t
    return Kind_map[kind](id, label, int1)

class ret:
    def __init__(self, symbol_id, label = None, int1 = None):
        self.id = symbol_id

    def gather_uses(self):
        crud.Db_cur.execute('''
            select tp.FIX
              from blocks b
                     inner join triples t
                        on b.id = t.block_id
                     inner join triple_parameters tp
                        on tp.parent_id = t.id
                       and tp.parameter_num = 1
             where b.word_symbol_id = ?
         ''', (self.id,))

class var(ret):
    def __init__(self, symbol_id, label, int1 = None):
        super().__init__(symbol_id)
        self.label = label

class parameter(var):
    def __init__(self, symbol_id, label, int1):
        super().__init__(symbol_id, label)
        self.param_num = int1

Kind_map = {
    'var': var,
    'parameter': parameter,
    'return': ret,
}
