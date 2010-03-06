# symbol_table.py

r'''Helpers for accessing the symbol_table table.
'''

from ucc.database import crud

Symbols = {}  #: {(label, context): `symbol`}, context is None or a `symbol`

Symbols_by_id = {}  #: {id: `symbol`}

unique = object()

def get(label, context = None, default = unique):
    r'''Get `symbol` by label.

    Error if not found and no 'default' given.
    '''
    if default is unique:
        return Symbols[label, context]
    return Symbols.get((label, context), default)

def get_by_id(id):
    r'''Get `symbol` by id.

    Error if not found.
    '''
    return Symbols_by_id[id]

def lookup(label, context = None):
    r'''Get `symbol` by label, create if not found.

    The symbol is created as kind='placeholder' which must be changed later.
    '''
    ans = get(label, context, None)
    if ans: return ans
    if context is not None:
        return lookup(label, context.context)
    return symbol.create(label, 'placeholder')

def write_symbols():
    r'''Write all symbols to the database.
    '''
    for sym in Symbols.itervalues():
        sym.write()

def update():
    r'''Update side_effects and suspends *from* database.
    '''
    for id in crud.read_column('symbol_table', 'id', side_effects=1):
        Symbols_by_id[id].side_effects = True
    for id in crud.read_column('symbol_table', 'id', suspends=1):
        Symbols_by_id[id].suspends = True

class symbol(object):
    r'''The class representing symbols in the compiler.
    '''
    doing_init = True   #: kludge for __setattr__
    side_effects = 0
    suspends = 0
    int1 = None
    word_word = None
    word_obj = None
    type_id = None

    def __init__(self, id, label, context = None, **attributes):
        r'''Not called directly.  Use `create` or `lookup` instead.
        '''
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

        Updates an existing database row (if found), or inserts a new row.

        Returns the id of the row.
        '''
        if context is None:
            id = crud.read1_column('symbol_table', 'id',
                                   label=label, context=None,
                                   zero_ok=True)
            if id is not None:
                crud.update('symbol_table', {'id': id}, kind=kind,
                            **attributes)
                if id in Symbols_by_id:
                    del Symbols_by_id[id]
                    del Symbols[label, None]
                return cls(id, label, context, kind=kind, **attributes)
        id = crud.insert('symbol_table',
                         option='replace',
                         label=label,
                         kind=kind,
                         context=context and context.id,
                         **attributes)
        return cls(id, label, context, kind=kind, **attributes)

    def __repr__(self):
        return "<symbol %s:%s>" % (self.id, self.label)

    def __setattr__(self, attr, value):
        r'''Gathers attributes that have changed for `write`.
        '''
        if self.doing_init:
            super(symbol, self).__setattr__(attr, value)
        else:
            assert attr not in ('id', 'label', 'context', 'updated_attrs',
                                'doing_init')
            super(symbol, self).__setattr__(attr, value)
            if attr not in ('word_word', 'word_obj'):
                self.updated_attrs.add(attr)

    def write(self):
        r'''Update database to reflect changes on this object.
        '''
        if self.updated_attrs:
            crud.update('symbol_table',
                        {'label': self.label,
                         'context': self.context and self.context.id},
                        **dict((attr, getattr(self, attr))
                               for attr in self.updated_attrs))
            self.updated_attrs.clear()
