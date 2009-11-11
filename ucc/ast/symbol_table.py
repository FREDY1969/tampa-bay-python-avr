# symbol_table.py

from ucc.ast import crud

class symbol(object):
    def __init__(self, **attributes):
        for name, value in attributes.iteritems():
            setattr(self, name, value)

    @classmethod
    def read(cls, name, context_id = None):
        r'''Reads name from symbol_table.

        Returns symbol object or None
        '''
        args = crud.read1_as_dict('symbol_table',
                                  context=context_id, name=name, zero_ok=True)
        if args is None: return None
        return cls(**args)

    @classmethod
    def create(cls, name, kind, context_id = None, **attributes):
        r'''Creates a new symbol_table entry.

        Updates an existing entry (if found), or inserts a new row.

        Returns the id of the row.
        '''
        ans = cls.read(name, context_id)
        if ans is not None: return ans
        crud.insert('symbol_table',
                    context=context_id, name=name, kind=kind,
                    **attributes)
        return cls.read(name, context_id)

    @classmethod
    def lookup(cls, name, context_id = None):
        ans = cls.read(name, context_id)
        if ans: return ans
        if context_id is None:
            id = crud.insert('symbol_table',
                             context=context_id, name=name, kind='placeholder')
            return cls(id=id, name=name, context=context_id, kind='placeholder')
        parent_id = crud.read1_column('symbol_table', 'context', id=context_id)
        return lookup(name, parent_id)
