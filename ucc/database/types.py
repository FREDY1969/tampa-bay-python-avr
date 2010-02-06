# types.py (not type.py since type is a Python builtin function).

r'''Classes for accessing types.

These go into the 'type' and 'sub_element' tables.

Prepare a couple of types first:

        >>> cur = crud.db_cur_test()

        >>> cur.lastrowid = 1
        >>> crud.dummy_transaction()
        >>> int.lookup(400, -100)
        query: insert into type (kind, max_value, min_value) values (?, ?, ?)
        parameters: ['int', 400, -100]
        <int 1>

        >>> cur.lastrowid = 2
        >>> fixedpt.lookup(400, -100, -2)
        query: insert into type (binary_pt, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [-2, 'fixedpt', 400, -100]
        <fixedpt 2>

'''

import itertools
from ucc.database import crud

Types_by_id = {}

def init():
    for row in crud.read_as_dicts('type'):
        getattr(globals(), row['kind']).from_db(row)

class base_type(object):
    def __init__(self, id, columns, sub_elements = None):
        self.id = id
        Types_by_id[id] = self
        for name, value in columns.iteritems():
            setattr(self, name, value)
        if sub_elements is not None:
            self.sub_elements = sub_elements

    @classmethod
    def add(cls, **columns):
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
                                           name=name, element_type=type.id)
        return cls(id, columns, sub_elements)

    @classmethod
    def from_db(cls, row):
        if 'element_type' in row and row['element_type'] is not None:
            row['element_type'] = Types_by_id[row['element_type']]
        key = cls.row_to_key(row)
        cls.Instances[key] = \
          cls(row['id'], dict((col, row['col']) for col in cls.Columns),
              cls.read_sub_elements(row, key))

    def __repr__(self):
        return "<%s %d>" % (self.__class__.__name__, self.id)

    @classmethod
    def lookup(cls, *args):
        key = cls.args_to_key(*args)
        if key not in cls.Instances:
            cls.verify_args(*args)
            cls.Instances[key] = cls.create(*args)
        return cls.Instances[key]

    @classmethod
    def args_to_key(cls, *args):
        return args

    @classmethod
    def row_to_key(cls, row):
        return tuple((Types_by_id[row[col]] if col == 'element_type'
                                            else row[col])
                     for col in cls.Columns)

    @classmethod
    def read_sub_elements(cls, row, key):
        return None

    @classmethod
    def verify_args(cls, *args):
        pass

    @classmethod
    def create(cls, *args):
        columns = dict(zip(cls.Columns, args))
        return cls.add(**columns)

    @classmethod
    def get_sub_elements(cls, row_id):
        return tuple((name, Types_by_id[element_type])
                     for name, element_type
                      in crud.read_as_tuples('sub_element',
                                             'name', 'element_type',
                                             parent_id=row_id,
                                             order_by=('element_order',)))

class int(base_type):
    r'''The class for 'int' types.

        >>> cur = crud.db_cur_test()

        >>> cur.lastrowid = 3
        >>> crud.dummy_transaction()
        >>> int.lookup(400, 100)
        query: insert into type (kind, max_value, min_value) values (?, ?, ?)
        parameters: ['int', 400, 100]
        <int 3>

        >>> int.lookup(400, 100)
        <int 3>

        >>> cur.lastrowid = 4
        >>> int.lookup(400, 10)
        query: insert into type (kind, max_value, min_value) values (?, ?, ?)
        parameters: ['int', 400, 10]
        <int 4>

        >>> cur.lastrowid = 5
        >>> int.lookup(410, 100)
        query: insert into type (kind, max_value, min_value) values (?, ?, ?)
        parameters: ['int', 410, 100]
        <int 5>

        >>> int.lookup(400, 100)
        <int 3>
        >>> int.lookup(400, 10)
        <int 4>
        >>> int.lookup(410, 100)
        <int 5>
    '''
    Instances = {}      # (max, min): int_obj
    Columns = ('max_value', 'min_value')

class fixedpt(base_type):
    r'''The class for 'fixept' types.

        >>> cur = crud.db_cur_test()

        >>> cur.lastrowid = 6
        >>> crud.dummy_transaction()
        >>> fixedpt.lookup(400, 100, -2)
        query: insert into type (binary_pt, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [-2, 'fixedpt', 400, 100]
        <fixedpt 6>

        >>> fixedpt.lookup(400, 100, -2)
        <fixedpt 6>

        >>> cur.lastrowid = 7
        >>> fixedpt.lookup(400, 10, -2)
        query: insert into type (binary_pt, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [-2, 'fixedpt', 400, 10]
        <fixedpt 7>

        >>> cur.lastrowid = 8
        >>> fixedpt.lookup(410, 100, -2)
        query: insert into type (binary_pt, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [-2, 'fixedpt', 410, 100]
        <fixedpt 8>

        >>> cur.lastrowid = 9
        >>> fixedpt.lookup(400, 100, -3)
        query: insert into type (binary_pt, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [-3, 'fixedpt', 400, 100]
        <fixedpt 9>

        >>> fixedpt.lookup(400, 100, -2)
        <fixedpt 6>
        >>> fixedpt.lookup(400, 10, -2)
        <fixedpt 7>
        >>> fixedpt.lookup(410, 100, -2)
        <fixedpt 8>
        >>> fixedpt.lookup(400, 100, -3)
        <fixedpt 9>
    '''
    Instances = {}      # (max, min): fixedpt_obj
    Columns = ('max_value', 'min_value', 'binary_pt')

class array(base_type):
    r'''The class for 'array' types.

        >>> cur = crud.db_cur_test()

        >>> int1_type = int.lookup(400, -100)
        >>> fixedpt1_type = fixedpt.lookup(400, -100, -2)

        >>> cur.lastrowid = 10
        >>> crud.dummy_transaction()
        >>> array.lookup(int1_type, 400, 100)
        query: insert into type (element_type, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [1, 'array', 400, 100]
        <array 10>

        >>> array.lookup(int1_type, 400, 100)
        <array 10>

        >>> cur.lastrowid = 11
        >>> array.lookup(int1_type, 400, 10)
        query: insert into type (element_type, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [1, 'array', 400, 10]
        <array 11>

        >>> cur.lastrowid = 12
        >>> array.lookup(int1_type, 410, 100)
        query: insert into type (element_type, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [1, 'array', 410, 100]
        <array 12>

        >>> cur.lastrowid = 13
        >>> array.lookup(fixedpt1_type, 400, 100)
        query: insert into type (element_type, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [2, 'array', 400, 100]
        <array 13>

        >>> array.lookup(int1_type, 400, 100)
        <array 10>
        >>> array.lookup(int1_type, 400, 10)
        <array 11>
        >>> array.lookup(int1_type, 410, 100)
        <array 12>
        >>> array.lookup(fixedpt1_type, 400, 100)
        <array 13>
    '''
    Instances = {}      # (element_type, max, min): array_obj
    Columns = ('element_type', 'max_value', 'min_value')

    @classmethod
    def verify_args(cls, element_type, max, min):
        assert min >= 0

class pointer(base_type):
    r'''The class for 'pointer' types.

        >>> cur = crud.db_cur_test()

        >>> int1_type = int.lookup(400, -100)
        >>> fixedpt1_type = fixedpt.lookup(400, -100, -2)

        >>> cur.lastrowid = 14
        >>> crud.dummy_transaction()
        >>> pointer.lookup(int1_type, 'ram')
        query: insert into type (element_type, kind, memory) values (?, ?, ?)
        parameters: [1, 'pointer', 'ram']
        <pointer 14>

        >>> pointer.lookup(int1_type, 'ram')
        <pointer 14>

        >>> cur.lastrowid = 15
        >>> pointer.lookup(int1_type, 'flash')
        query: insert into type (element_type, kind, memory) values (?, ?, ?)
        parameters: [1, 'pointer', 'flash']
        <pointer 15>

        >>> cur.lastrowid = 16
        >>> pointer.lookup(fixedpt1_type, 'ram')
        query: insert into type (element_type, kind, memory) values (?, ?, ?)
        parameters: [2, 'pointer', 'ram']
        <pointer 16>

        >>> cur.lastrowid = 17
        >>> pointer.lookup(fixedpt1_type, 'flash')
        query: insert into type (element_type, kind, memory) values (?, ?, ?)
        parameters: [2, 'pointer', 'flash']
        <pointer 17>

        >>> pointer.lookup(int1_type, 'ram')
        <pointer 14>
        >>> pointer.lookup(int1_type, 'flash')
        <pointer 15>
        >>> pointer.lookup(fixedpt1_type, 'ram')
        <pointer 16>
        >>> pointer.lookup(fixedpt1_type, 'flash')
        <pointer 17>
    '''
    Instances = {}      # (element_type, memory): pointer_obj
    Columns = ('element_type', 'memory')

class record(base_type):
    r'''The class for 'record' types.

        >>> cur = crud.db_cur_test()

        >>> int1_type = int.lookup(400, -100)
        >>> fixedpt1_type = fixedpt.lookup(400, -100, -2)

        >>> cur.lastrowid = 18
        >>> crud.dummy_transaction()
        >>> record.lookup(('foo', int1_type), ('bar', int1_type))
        query: insert into type (kind) values (?)
        parameters: ['record']
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [0, 1, 'foo', 18]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [1, 1, 'bar', 18]
        <record 18>

        >>> record.lookup(('foo', int1_type), ('bar', int1_type))
        <record 18>

        >>> cur.lastrowid = 19
        >>> record.lookup(('foo', int1_type), ('bar', fixedpt1_type))
        query: insert into type (kind) values (?)
        parameters: ['record']
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [0, 1, 'foo', 19]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [1, 2, 'bar', 19]
        <record 19>

        >>> cur.lastrowid = 20
        >>> record.lookup(('foo', int1_type), ('baz', int1_type))
        query: insert into type (kind) values (?)
        parameters: ['record']
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [0, 1, 'foo', 20]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [1, 1, 'baz', 20]
        <record 20>

        >>> cur.lastrowid = 21
        >>> record.lookup(('foo', int1_type))
        query: insert into type (kind) values (?)
        parameters: ['record']
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [0, 1, 'foo', 21]
        <record 21>

        >>> record.lookup(('foo', int1_type), ('bar', int1_type))
        <record 18>
        >>> record.lookup(('foo', int1_type), ('bar', fixedpt1_type))
        <record 19>
        >>> record.lookup(('foo', int1_type), ('baz', int1_type))
        <record 20>
        >>> record.lookup(('foo', int1_type))
        <record 21>
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

class function(base_type):
    r'''The class for 'function' types.

        >>> cur = crud.db_cur_test()

        >>> int1_type = int.lookup(400, -100)
        >>> fixedpt1_type = fixedpt.lookup(400, -100, -2)

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
        <function 22>

        >>> function.lookup(int1_type, (('foo', int1_type), ('bar', int1_type)),
        ...                            ())
        <function 22>

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
        <function 23>

        >>> cur.lastrowid = 24
        >>> function.lookup(int1_type, (('foo', int1_type),),
        ...                            (('bar', int1_type),))
        query: insert into type (element_type, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [1, 'function', 2, 1]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [0, 1, 'foo', 24]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [1, 1, 'bar', 24]
        <function 24>

        >>> cur.lastrowid = 25
        >>> function.lookup(int1_type, (), (('foo', int1_type),
        ...                                 ('bar', int1_type)))
        query: insert into type (element_type, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [1, 'function', 2, 0]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [0, 1, 'foo', 25]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [1, 1, 'bar', 25]
        <function 25>

        >>> cur.lastrowid = 26
        >>> function.lookup(int1_type, (), (('foo', int1_type),
        ...                                 ('bar', fixedpt1_type)))
        query: insert into type (element_type, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [1, 'function', 2, 0]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [0, 1, 'foo', 26]
        query: insert into sub_element (element_order, element_type, name, parent_id) values (?, ?, ?, ?)
        parameters: [1, 2, 'bar', 26]
        <function 26>

        >>> function.lookup(int1_type, (('foo', int1_type), ('bar', int1_type)), ())
        <function 22>
        >>> function.lookup(fixedpt1_type, (('foo', int1_type), ('bar', int1_type)), ())
        <function 23>
        >>> function.lookup(int1_type, (('foo', int1_type),),
        ...                            (('bar', int1_type),))
        <function 24>
        >>> function.lookup(int1_type, (), (('foo', int1_type),
        ...                                 ('bar', int1_type)))
        <function 25>
        >>> function.lookup(int1_type, (), (('foo', int1_type),
        ...                                 ('bar', fixedpt1_type)))
        <function 26>
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

