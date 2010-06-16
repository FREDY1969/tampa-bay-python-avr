# ucl_types.py
# (not type.py since type is a Python builtin function).
# (not types.py since types is a standard Python library module).

r'''Classes for accessing types.

These go into the 'type' and 'sub_element' tables.

All type objects are immutable.  They are inserted into the database when the
object is created, and never updated after that.

Prepare a couple of types for the rest of the doctests:

        >>> cur = crud.db_cur_test()

        >>> crud.dummy_transaction()
        >>> cur.description = (('kind',),)
        >>> cur.answers = []
        >>> init()
        query: select * from type
        parameters: []
        >>> cur.lastrowid = 1
        >>> int.lookup(-100, 400)
        query: insert into type (kind, max_value, min_value) values (?, ?, ?)
        parameters: ['int', 400, -100]
        <int:1 -100-400>

        >>> cur.lastrowid = 2
        >>> fixedpt.lookup(-100, 400, -2)
        query: insert into type (binary_pt, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [-2, 'fixedpt', 400, -100]
        <fixedpt:2 -100-400.-2>

'''

import itertools
from ucc.database import crud

#Types_by_id = {}        #: {id: type object}

def init():
    r'''Reads the types in from database.

    This ensures that references to the same type will have the same type id
    as prior runs of the compiler.
    '''
    global Types_by_id
    Types_by_id = {}        #: {id: type object}
    for row in crud.read_as_dicts('type'):
        getattr(globals(), row['kind']).from_db(row)

class base_type:
    r'''Base class for all types.
    '''
    def __init__(self, id, columns, sub_elements = None):
        r'''Not called directly.  Call `lookup` or `from_db` instead.
        '''
        self.id = id
        Types_by_id[id] = self
        for name, value in columns.items():
            setattr(self, name, value)
        if sub_elements is not None:
            self.sub_elements = sub_elements

    @classmethod
    def add(cls, **columns):
        r'''Internal method called by `create`.

        This inserts the new type (and sub_elements, if any) into the
        database.

        This method is shared by all base classes.
        '''
        sub_elements = None
        if 'sub_elements' in columns:
            sub_elements = columns['sub_elements']
            del columns['sub_elements']
        insert_columns = columns.copy()
        if 'element_type' in insert_columns:
            insert_columns['element_type'] = insert_columns['element_type'].id
        id = crud.insert('type', kind=cls.__name__, **insert_columns)
        if sub_elements:
            for i, field in enumerate(sub_elements):
                if isinstance(field, base_type):
                    name = None
                    type = field
                else:
                    name, type = field
                crud.insert('sub_element', parent_id=id, element_order=i,
                                           name=name, element_type=type)
        return cls(id, columns, sub_elements)

    @classmethod
    def from_db(cls, row):
        r'''Internal method called by `init`.

        Figures out what is needed from row and creates the object instance.
        '''
        if 'element_type' in row and row['element_type'] is not None:
            row['element_type'] = Types_by_id[row['element_type']]
        key = cls.row_to_key(row)
        cls.Instances[key] = \
          cls(row['id'], dict((col, row['col']) for col in cls.Columns),
              cls.read_sub_elements(row, key))

    @classmethod
    def lookup(cls, *args):
        r'''Lookup a type.

        The type is created if it does not already exist.

        This is called on the derived class to determine what kind of type is
        wanted.  Each derived class defines a different set of 'args'.  The
        'args' expected are the arguments to the derived class' `create`
        method.
        '''
        key = cls.args_to_key(*args)
        if key not in cls.Instances:
            cls.verify_args(*args)
            cls.Instances[key] = cls.create(*args)
        return cls.Instances[key]

    @classmethod
    def args_to_key(cls, *args):
        r'''Internal method called by `lookup`.

        Returns the key to the cls.Instances dictionary.

        This may be overridden by base classes.
        '''
        return args

    @classmethod
    def row_to_key(cls, row):
        r'''Internal method called by `from_db`.

        Returns the key to the cls.Instances dictionary.

        This may be overridden by base classes.
        '''
        return tuple((Types_by_id[row[col]] if col == 'element_type'
                                            else row[col])
                     for col in cls.Columns)

    @classmethod
    def read_sub_elements(cls, row, key):
        r'''Internal method called by `from_db`.

        Returns the value to be stored in self.sub_elements.  This is either a
        tuple of (name, type) pairs, or None.

        This may be overridden by base classes.
        '''
        return None

    @classmethod
    def verify_args(cls, *args):
        r'''Internal method called by `lookup`.

        Raises an exception if the validation fails.

        Does not return anything.

        This may be overridden by base classes.
        '''
        pass

    @classmethod
    def create(cls, *args):
        r'''Internal method called by `lookup`.

        Calls `add` with the proper arguments for this class.

        This may be overridden by base classes.
        '''
        columns = dict(list(zip(cls.Columns, args)))
        return cls.add(**columns)

    @classmethod
    def get_sub_elements(cls, row_id):
        r'''Internal method called by `row_to_key` in derived classes.

        Reads the sub_elements from the database and returns a tuple of (name,
        type) tuples.

        This method is shared by all base classes.
        '''
        return tuple((name, Types_by_id[element_type])
                     for name, element_type
                      in crud.read_as_tuples('sub_element',
                                             'name', 'element_type',
                                             parent_id=row_id,
                                             order_by=('element_order',)))

class int(base_type):
    r'''The class for 'int' types.

    Use lookup(min_value, max_value).

        >>> cur = crud.db_cur_test()

        >>> cur.lastrowid = 3
        >>> crud.dummy_transaction()
        >>> int.lookup(100, 400)
        query: insert into type (kind, max_value, min_value) values (?, ?, ?)
        parameters: ['int', 400, 100]
        <int:3 100-400>

        >>> int.lookup(100, 400)
        <int:3 100-400>

        >>> cur.lastrowid = 4
        >>> int.lookup(10, 400)
        query: insert into type (kind, max_value, min_value) values (?, ?, ?)
        parameters: ['int', 400, 10]
        <int:4 10-400>

        >>> cur.lastrowid = 5
        >>> int.lookup(100, 410)
        query: insert into type (kind, max_value, min_value) values (?, ?, ?)
        parameters: ['int', 410, 100]
        <int:5 100-410>

        >>> int.lookup(100, 400)
        <int:3 100-400>
        >>> int.lookup(10, 400)
        <int:4 10-400>
        >>> int.lookup(100, 410)
        <int:5 100-410>
    '''
    Instances = {}      # (max, min): int_obj
    Columns = ('min_value', 'max_value')

    def __repr__(self):
        return "<int:{} {}-{}>".format(self.id, self.min_value, self.max_value)

class fixedpt(base_type):
    r'''The class for 'fixept' types.

    Use lookup(min_value, max_value, binary_pt).

        >>> cur = crud.db_cur_test()

        >>> cur.lastrowid = 6
        >>> crud.dummy_transaction()
        >>> fixedpt.lookup(100, 400, -2)
        query: insert into type (binary_pt, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [-2, 'fixedpt', 400, 100]
        <fixedpt:6 100-400.-2>

        >>> fixedpt.lookup(100, 400, -2)
        <fixedpt:6 100-400.-2>

        >>> cur.lastrowid = 7
        >>> fixedpt.lookup(10, 400, -2)
        query: insert into type (binary_pt, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [-2, 'fixedpt', 400, 10]
        <fixedpt:7 10-400.-2>

        >>> cur.lastrowid = 8
        >>> fixedpt.lookup(100, 410, -2)
        query: insert into type (binary_pt, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [-2, 'fixedpt', 410, 100]
        <fixedpt:8 100-410.-2>

        >>> cur.lastrowid = 9
        >>> fixedpt.lookup(100, 400, -3)
        query: insert into type (binary_pt, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [-3, 'fixedpt', 400, 100]
        <fixedpt:9 100-400.-3>

        >>> fixedpt.lookup(100, 400, -2)
        <fixedpt:6 100-400.-2>
        >>> fixedpt.lookup(10, 400, -2)
        <fixedpt:7 10-400.-2>
        >>> fixedpt.lookup(100, 410, -2)
        <fixedpt:8 100-410.-2>
        >>> fixedpt.lookup(100, 400, -3)
        <fixedpt:9 100-400.-3>
    '''
    Instances = {}      # (max, min): fixedpt_obj
    Columns = ('min_value', 'max_value', 'binary_pt')

    def __repr__(self):
        return "<fixedpt:{} {}-{}.{}>" \
                 .format(self.id, self.min_value, self.max_value,
                         self.binary_pt)

class array(base_type):
    r'''The class for 'array' types.

    Use lookup(element_type, min_value, max_value).

        >>> cur = crud.db_cur_test()

        >>> int1_type = int.lookup(-100, 400)
        >>> fixedpt1_type = fixedpt.lookup(-100, 400, -2)

        >>> cur.lastrowid = 10
        >>> crud.dummy_transaction()
        >>> array.lookup(int1_type, 100, 400)
        query: insert into type (element_type, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [1, 'array', 400, 100]
        <array:10 100-400 of <int:1 -100-400>>

        >>> array.lookup(int1_type, 100, 400)
        <array:10 100-400 of <int:1 -100-400>>

        >>> cur.lastrowid = 11
        >>> array.lookup(int1_type, 10, 400)
        query: insert into type (element_type, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [1, 'array', 400, 10]
        <array:11 10-400 of <int:1 -100-400>>

        >>> cur.lastrowid = 12
        >>> array.lookup(int1_type, 100, 410)
        query: insert into type (element_type, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [1, 'array', 410, 100]
        <array:12 100-410 of <int:1 -100-400>>

        >>> cur.lastrowid = 13
        >>> array.lookup(fixedpt1_type, 100, 400)
        query: insert into type (element_type, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [2, 'array', 400, 100]
        <array:13 100-400 of <fixedpt:2 -100-400.-2>>

        >>> array.lookup(int1_type, 100, 400)
        <array:10 100-400 of <int:1 -100-400>>
        >>> array.lookup(int1_type, 10, 400)
        <array:11 10-400 of <int:1 -100-400>>
        >>> array.lookup(int1_type, 100, 410)
        <array:12 100-410 of <int:1 -100-400>>
        >>> array.lookup(fixedpt1_type, 100, 400)
        <array:13 100-400 of <fixedpt:2 -100-400.-2>>
    '''
    Instances = {}      # (element_type, max, min): array_obj
    Columns = ('element_type', 'min_value', 'max_value')

    @classmethod
    def verify_args(cls, element_type, min, max):
        assert min >= 0

    def __repr__(self):
        return "<array:{} {}-{} of {}>" \
                 .format(self.id, self.min_value, self.max_value,
                         repr(self.element_type))

class pointer(base_type):
    r'''The class for 'pointer' types.

    Use lookup(element_type, memory).

        >>> cur = crud.db_cur_test()

        >>> int1_type = int.lookup(-100, 400)
        >>> fixedpt1_type = fixedpt.lookup(-100, 400, -2)

        >>> cur.lastrowid = 14
        >>> crud.dummy_transaction()
        >>> pointer.lookup(int1_type, 'ram')
        query: insert into type (element_type, kind, memory) values (?, ?, ?)
        parameters: [1, 'pointer', 'ram']
        <pointer:14 ram to <int:1 -100-400>>

        >>> pointer.lookup(int1_type, 'ram')
        <pointer:14 ram to <int:1 -100-400>>

        >>> cur.lastrowid = 15
        >>> pointer.lookup(int1_type, 'flash')
        query: insert into type (element_type, kind, memory) values (?, ?, ?)
        parameters: [1, 'pointer', 'flash']
        <pointer:15 flash to <int:1 -100-400>>

        >>> cur.lastrowid = 16
        >>> pointer.lookup(fixedpt1_type, 'ram')
        query: insert into type (element_type, kind, memory) values (?, ?, ?)
        parameters: [2, 'pointer', 'ram']
        <pointer:16 ram to <fixedpt:2 -100-400.-2>>

        >>> cur.lastrowid = 17
        >>> pointer.lookup(fixedpt1_type, 'flash')
        query: insert into type (element_type, kind, memory) values (?, ?, ?)
        parameters: [2, 'pointer', 'flash']
        <pointer:17 flash to <fixedpt:2 -100-400.-2>>

        >>> pointer.lookup(int1_type, 'ram')
        <pointer:14 ram to <int:1 -100-400>>
        >>> pointer.lookup(int1_type, 'flash')
        <pointer:15 flash to <int:1 -100-400>>
        >>> pointer.lookup(fixedpt1_type, 'ram')
        <pointer:16 ram to <fixedpt:2 -100-400.-2>>
        >>> pointer.lookup(fixedpt1_type, 'flash')
        <pointer:17 flash to <fixedpt:2 -100-400.-2>>
    '''
    Instances = {}      # (element_type, memory): pointer_obj
    Columns = ('element_type', 'memory')

    def __repr__(self):
        return "<pointer:{} {} to {}>" \
                 .format(self.id, self.memory, repr(self.element_type))

class record(base_type):
    r'''The class for 'record' types.

    Use lookup((field_name, type), ...).

        >>> cur = crud.db_cur_test()

        >>> int1_type = int.lookup(-100, 400)
        >>> fixedpt1_type = fixedpt.lookup(-100, 400, -2)

        >>> cur.lastrowid = 18
        >>> crud.dummy_transaction()
        >>> record.lookup(('foo', int1_type), ('bar', int1_type))
        query: insert into type (kind) values (?)
        parameters: ['record']
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [0, 1, 'foo', 18]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [1, 1, 'bar', 18]
        <record:18>

        >>> record.lookup(('foo', int1_type), ('bar', int1_type))
        <record:18>

        >>> cur.lastrowid = 19
        >>> record.lookup(('foo', int1_type), ('bar', fixedpt1_type))
        query: insert into type (kind) values (?)
        parameters: ['record']
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [0, 1, 'foo', 19]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [1, 2, 'bar', 19]
        <record:19>

        >>> cur.lastrowid = 20
        >>> record.lookup(('foo', int1_type), ('baz', int1_type))
        query: insert into type (kind) values (?)
        parameters: ['record']
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [0, 1, 'foo', 20]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [1, 1, 'baz', 20]
        <record:20>

        >>> cur.lastrowid = 21
        >>> record.lookup(('foo', int1_type))
        query: insert into type (kind) values (?)
        parameters: ['record']
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [0, 1, 'foo', 21]
        <record:21>

        >>> record.lookup(('foo', int1_type), ('bar', int1_type))
        <record:18>
        >>> record.lookup(('foo', int1_type), ('bar', fixedpt1_type))
        <record:19>
        >>> record.lookup(('foo', int1_type), ('baz', int1_type))
        <record:20>
        >>> record.lookup(('foo', int1_type))
        <record:21>
    '''
    Instances = {}      # ((name, element_type), ...): record_type
    Columns = ()

    @classmethod
    def create(cls, *fields):
        return cls.add(sub_elements=fields)

    @classmethod
    def row_to_key(cls, row):
        return cls.get_sub_elements(row['id'])

    @classmethod
    def read_sub_elements(cls, row, key):
        return key

    def __repr__(self):
        return "<record:{}>".format(self.id)

class function(base_type):
    r'''The class for 'function' types.

    Use::

        lookup(return_type,
               ((required_param_name, type), ...),
               ((optional_param_name, type), ...))

    Examples:

        >>> cur = crud.db_cur_test()

        >>> int1_type = int.lookup(-100, 400)
        >>> fixedpt1_type = fixedpt.lookup(-100, 400, -2)

        >>> cur.lastrowid = 22
        >>> crud.dummy_transaction()
        >>> function.lookup(int1_type, (('foo', int1_type), ('bar', int1_type)),
        ...                            ())
        query: insert into type (element_type, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [1, 'function', 2, 2]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [0, 1, 'foo', 22]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [1, 1, 'bar', 22]
        <function:22 returning <int:1 -100-400>>

        >>> function.lookup(int1_type, (('foo', int1_type), ('bar', int1_type)),
        ...                            ())
        <function:22 returning <int:1 -100-400>>

        >>> cur.lastrowid = 23
        >>> function.lookup(fixedpt1_type, (('foo', int1_type),
        ...                                 ('bar', int1_type)),
        ...                                ())
        query: insert into type (element_type, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [2, 'function', 2, 2]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [0, 1, 'foo', 23]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [1, 1, 'bar', 23]
        <function:23 returning <fixedpt:2 -100-400.-2>>

        >>> cur.lastrowid = 24
        >>> function.lookup(int1_type, (('foo', int1_type),),
        ...                            (('bar', int1_type),))
        query: insert into type (element_type, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [1, 'function', 2, 1]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [0, 1, 'foo', 24]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [1, 1, 'bar', 24]
        <function:24 returning <int:1 -100-400>>

        >>> cur.lastrowid = 25
        >>> function.lookup(int1_type, (), (('foo', int1_type),
        ...                                 ('bar', int1_type)))
        query: insert into type (element_type, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [1, 'function', 2, 0]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [0, 1, 'foo', 25]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [1, 1, 'bar', 25]
        <function:25 returning <int:1 -100-400>>

        >>> cur.lastrowid = 26
        >>> function.lookup(int1_type, (), (('foo', int1_type),
        ...                                 ('bar', fixedpt1_type)))
        query: insert into type (element_type, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [1, 'function', 2, 0]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [0, 1, 'foo', 26]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [1, 2, 'bar', 26]
        <function:26 returning <int:1 -100-400>>

        >>> function.lookup(int1_type, (('foo', int1_type), ('bar', int1_type)), ())
        <function:22 returning <int:1 -100-400>>
        >>> function.lookup(fixedpt1_type, (('foo', int1_type), ('bar', int1_type)), ())
        <function:23 returning <fixedpt:2 -100-400.-2>>
        >>> function.lookup(int1_type, (('foo', int1_type),),
        ...                            (('bar', int1_type),))
        <function:24 returning <int:1 -100-400>>
        >>> function.lookup(int1_type, (), (('foo', int1_type),
        ...                                 ('bar', int1_type)))
        <function:25 returning <int:1 -100-400>>
        >>> function.lookup(int1_type, (), (('foo', int1_type),
        ...                                 ('bar', fixedpt1_type)))
        <function:26 returning <int:1 -100-400>>
    '''
    Instances = {}      # (ret_type, req_arg_types, opt_arg_types): function_obj
    Columns = ('element_type',)

    @classmethod
    def create(cls, ret, req_arg_types, opt_arg_types):
        return cls.add(element_type=ret,
                       min_value=len(req_arg_types),
                       max_value=len(req_arg_types) + len(opt_arg_types),
                       sub_elements=itertools.chain(req_arg_types,
                                                    opt_arg_types))

    @classmethod
    def row_to_key(cls, row):
        args = cls.get_sub_elements(row['id'])
        return (Types_by_id[row['element_type']],
                args[:row['min_value']],
                args[row['min_value']:])

    @classmethod
    def read_sub_elements(cls, row, key):
        ret_type, req_args, opt_args = key
        return req_args + opt_args

    def __repr__(self):
        return "<function:{} returning {}>".format(self.id, self.element_type)

