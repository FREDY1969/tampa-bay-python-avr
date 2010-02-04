# types.py (not type.py since type is a Python builtin function).

r'''Classes for accessing types.

These go into the 'type' and 'sub_element' tables.

Prepare a couple of types first:

        >>> cur = crud.db_cur_test()

        >>> cur.lastrowid = 1
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

class base_type(object):
    def __init__(self, **columns):
        for name, value in columns.iteritems():
            setattr(self, name, value)
        sub_elements = None
        if 'sub_elements' in columns:
            sub_elements = columns['sub_elements']
            del columns['sub_elements']
        self.id = crud.insert('type', **columns)
        if sub_elements:
            for i, field in enumerate(sub_elements):
                if isinstance(field, base_type):
                    name = None
                    type = field
                else:
                    name, type = field
                crud.insert('sub_element', parent_id=self.id, order=i,
                                           name=name, element_type=type.id)

    def __repr__(self):
        return "<%s %d>" % (self.__class__.__name__, self.id)

    @classmethod
    def lookup(cls, *args):
        key = cls.key(*args)
        if key not in cls.Instances:
            cls.Instances[key] = cls.create(*args)
        return cls.Instances[key]

    @classmethod
    def key(cls, *args):
        return args

class int(base_type):
    r'''The class for 'int' types.

        >>> cur = crud.db_cur_test()

        >>> cur.lastrowid = 3
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

    @classmethod
    def create(cls, max, min):
        return cls(kind='int', max_value=max, min_value=min)

class fixedpt(base_type):
    r'''The class for 'fixept' types.

        >>> cur = crud.db_cur_test()

        >>> cur.lastrowid = 6
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

    @classmethod
    def create(cls, max, min, binary_pt):
        return cls(kind='fixedpt', max_value=max, min_value=min,
                   binary_pt=binary_pt)

class array(base_type):
    r'''The class for 'array' types.

        >>> cur = crud.db_cur_test()

        >>> int1_type = int.lookup(400, -100)
        >>> fixedpt1_type = fixedpt.lookup(400, -100, -2)

        >>> cur.lastrowid = 10
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

    @classmethod
    def create(cls, element_type, max, min):
        assert min >= 0
        return cls(kind='array', element_type=element_type.id,
                   max_value=max, min_value=min)

class pointer(base_type):
    r'''The class for 'pointer' types.

        >>> cur = crud.db_cur_test()

        >>> int1_type = int.lookup(400, -100)
        >>> fixedpt1_type = fixedpt.lookup(400, -100, -2)

        >>> cur.lastrowid = 14
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

    @classmethod
    def create(cls, element_type, memory):
        return cls(kind='pointer', element_type=element_type.id, memory=memory)

class record(base_type):
    r'''The class for 'record' types.

        >>> cur = crud.db_cur_test()

        >>> int1_type = int.lookup(400, -100)
        >>> fixedpt1_type = fixedpt.lookup(400, -100, -2)

        >>> cur.lastrowid = 18
        >>> record.lookup(('foo', int1_type), ('bar', int1_type))
        query: insert into type (kind) values (?)
        parameters: ['record']
        query: insert into sub_element (element_type, name, order, parent_id) values (?, ?, ?, ?)
        parameters: [1, 'foo', 0, 18]
        query: insert into sub_element (element_type, name, order, parent_id) values (?, ?, ?, ?)
        parameters: [1, 'bar', 1, 18]
        <record 18>

        >>> record.lookup(('foo', int1_type), ('bar', int1_type))
        <record 18>

        >>> cur.lastrowid = 19
        >>> record.lookup(('foo', int1_type), ('bar', fixedpt1_type))
        query: insert into type (kind) values (?)
        parameters: ['record']
        query: insert into sub_element (element_type, name, order, parent_id) values (?, ?, ?, ?)
        parameters: [1, 'foo', 0, 19]
        query: insert into sub_element (element_type, name, order, parent_id) values (?, ?, ?, ?)
        parameters: [2, 'bar', 1, 19]
        <record 19>

        >>> cur.lastrowid = 20
        >>> record.lookup(('foo', int1_type), ('baz', int1_type))
        query: insert into type (kind) values (?)
        parameters: ['record']
        query: insert into sub_element (element_type, name, order, parent_id) values (?, ?, ?, ?)
        parameters: [1, 'foo', 0, 20]
        query: insert into sub_element (element_type, name, order, parent_id) values (?, ?, ?, ?)
        parameters: [1, 'baz', 1, 20]
        <record 20>

        >>> cur.lastrowid = 21
        >>> record.lookup(('foo', int1_type))
        query: insert into type (kind) values (?)
        parameters: ['record']
        query: insert into sub_element (element_type, name, order, parent_id) values (?, ?, ?, ?)
        parameters: [1, 'foo', 0, 21]
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

    @classmethod
    def create(cls, *fields):
        return cls(kind='record', sub_elements=fields)

class function(base_type):
    r'''The class for 'function' types.

        >>> cur = crud.db_cur_test()

        >>> int1_type = int.lookup(400, -100)
        >>> fixedpt1_type = fixedpt.lookup(400, -100, -2)

        >>> cur.lastrowid = 22
        >>> function.lookup(int1_type, (('foo', int1_type), ('bar', int1_type)), ())
        query: insert into type (element_type, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [1, 'function', 2, 2]
        query: insert into sub_element (element_type, name, order, parent_id) values (?, ?, ?, ?)
        parameters: [1, 'foo', 0, 22]
        query: insert into sub_element (element_type, name, order, parent_id) values (?, ?, ?, ?)
        parameters: [1, 'bar', 1, 22]
        <function 22>

        >>> function.lookup(int1_type, (('foo', int1_type), ('bar', int1_type)), ())
        <function 22>

        >>> cur.lastrowid = 23
        >>> function.lookup(fixedpt1_type, (('foo', int1_type), ('bar', int1_type)), ())
        query: insert into type (element_type, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [2, 'function', 2, 2]
        query: insert into sub_element (element_type, name, order, parent_id) values (?, ?, ?, ?)
        parameters: [1, 'foo', 0, 23]
        query: insert into sub_element (element_type, name, order, parent_id) values (?, ?, ?, ?)
        parameters: [1, 'bar', 1, 23]
        <function 23>

        >>> cur.lastrowid = 24
        >>> function.lookup(int1_type, (('foo', int1_type),),
        ...                            (('bar', int1_type),))
        query: insert into type (element_type, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [1, 'function', 2, 1]
        query: insert into sub_element (element_type, name, order, parent_id) values (?, ?, ?, ?)
        parameters: [1, 'foo', 0, 24]
        query: insert into sub_element (element_type, name, order, parent_id) values (?, ?, ?, ?)
        parameters: [1, 'bar', 1, 24]
        <function 24>

        >>> cur.lastrowid = 25
        >>> function.lookup(int1_type, (), (('foo', int1_type),
        ...                                 ('bar', int1_type)))
        query: insert into type (element_type, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [1, 'function', 2, 0]
        query: insert into sub_element (element_type, name, order, parent_id) values (?, ?, ?, ?)
        parameters: [1, 'foo', 0, 25]
        query: insert into sub_element (element_type, name, order, parent_id) values (?, ?, ?, ?)
        parameters: [1, 'bar', 1, 25]
        <function 25>

        >>> cur.lastrowid = 26
        >>> function.lookup(int1_type, (), (('foo', int1_type),
        ...                                 ('bar', fixedpt1_type)))
        query: insert into type (element_type, kind, max_value, min_value) values (?, ?, ?, ?)
        parameters: [1, 'function', 2, 0]
        query: insert into sub_element (element_type, name, order, parent_id) values (?, ?, ?, ?)
        parameters: [1, 'foo', 0, 26]
        query: insert into sub_element (element_type, name, order, parent_id) values (?, ?, ?, ?)
        parameters: [2, 'bar', 1, 26]
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

    @classmethod
    def create(cls, ret, req_arg_types, opt_arg_types):
        return cls(kind='function', element_type=ret.id,
                   min_value=len(req_arg_types),
                   max_value=len(req_arg_types) + len(opt_arg_types),
                   sub_elements=itertools.chain(req_arg_types, opt_arg_types))

