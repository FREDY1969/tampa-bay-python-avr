# symbol_table.py

from ucc.database import crud

Symbols = {}            # {(label, context): symbol}
                        #   where context is None or a symbol

Symbols_by_id = {}      # {id: symbol}

def get(label, context = None):
    return Symbols.get((label, context))

def get_by_id(id):
    return Symbols_by_id[id]

def lookup(label, context = None):
    ans = get(label, context)
    if ans: return ans
    if context is not None:
        return lookup(label, context.context)
    return symbol.create(label, 'placeholder')

def write_symbols():
    for sym in Symbols.itervalues():
        sym.write()

class symbol(object):
    doing_init = True
    def __init__(self, id, label, context = None, **attributes):
        self.id = id
        self.label = label
        self.context = context
        for name, value in attributes.iteritems():
            setattr(self, name, value)
        self.updated_attrs = set()
        assert (self.label, self.context) not in Symbols, \
               "symbol %s%s created twice" % \
                 (self.context.label + '.' if self.context else '',
                  self.label)
        Symbols[label, context] = self
        Symbols_by_id[self.id] = self
        self.doing_init = False

    @classmethod
    def create(cls, label, kind, context = None, **attributes):
        r'''Creates a new symbol_table entry.

        Updates an existing entry (if found), or inserts a new row.

        Returns the id of the row.
        '''
        id = crud.insert('symbol_table',
                         label=label,
                         kind=kind,
                         context=context and context.id,
                         **attributes)
        return cls(id, label, context, kind=kind, **attributes)

    def __repr__(self):
        return "<symbol %s:%s>" % (self.id, self.label)

    def __setattr__(self, attr, value):
        if self.doing_init:
            super(symbol, self).__setattr__(attr, value)
        else:
            assert attr not in ('id', 'label', 'context', 'updated_attrs',
                                'doing_init')
            super(symbol, self).__setattr__(attr, value)
            self.updated_attrs.add(attr)

    def write(self):
        if self.updated_attrs:
            crud.update('symbol_table',
                        {'label': self.label,
                         'context': context and context.id},
                        **dict((attr, getattr(self, attr))
                               for attr in self.updated_attrs))
            self.updated_attrs.clear()
