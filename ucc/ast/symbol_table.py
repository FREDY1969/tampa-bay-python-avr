# symbol_table.py

from ucc.ast import crud

class symbol(object):
    def __init__(self, **attributes):
        for name, value in attributes.iteritems():
            setattr(self, name, value)

    @classmethod
    def read(cls, label, context_id = None):
        r'''Reads label from symbol_table.

        Returns symbol object or None
        '''
        args = crud.read1_as_dict('symbol_table',
                                  context=context_id, label=label, zero_ok=True)
        if args is None: return None
        return cls(**args)

    @classmethod
    def create(cls, label, kind, context_id = None, **attributes):
        r'''Creates a new symbol_table entry.

        Updates an existing entry (if found), or inserts a new row.

        Returns the id of the row.
        '''
        ans = cls.read(label, context_id)
        if ans is not None: return ans
        crud.insert('symbol_table',
                    context=context_id, label=label, kind=kind,
                    **attributes)
        return cls.read(label, context_id)

    @classmethod
    def lookup(cls, label, context_id = None):
        ans = cls.read(label, context_id)
        if ans: return ans
        if context_id is None:
            id = crud.insert('symbol_table',
                             context=context_id, label=label,
                             kind='placeholder')
            return cls(id=id, label=label, context=context_id,
                       kind='placeholder')
        parent_id = crud.read1_column('symbol_table', 'context', id=context_id)
        return cls.lookup(label, parent_id)