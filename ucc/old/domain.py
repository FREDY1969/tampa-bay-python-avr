# domain.py

class domain(object):
    def type(self): return self.__class__.__name__

class type(domain):
    def __init__(self, max, min = 0):
        self.max = max
        self.min = min

class number(type):
    pass

class any_precision(number):
    def __repr__(self):
        return "<precise %r-%r>" % (self.min, self.max)

class fixed_precision(number):
    def __init__(self, max, min, binary_pt, precision):
        super(fixed_precision, self).__init__(max, min)
        self.binary_pt = binary_pt
        self.precision = precision
    def __repr__(self):
        return "<approx %r-%r .%r ~%r>" % \
                 (self.min, self.max, self.binary_pt, self.precision)

class array(type):
    r''' Max, min refer to the length of the array. '''
    def __init__(self, max, min, element_type):
        super(array, self).__init__(max, min)
        self.element_type = element_type
    def __repr__(self):
        return "<%s %r-%r of %r>" % \
                 (self.__class__.__name__, self.min, self.max,
                  self.element_type)

class Parray(array):
    pass

class string(array):
    r''' Max, min refer to the length of the string. '''
    def __init__(self, max, min):
        super(string, self).__init__(max, min, byte)
    def __repr__(self):
        return "<%s %r-%r>" % (self.__class__.__name__, self.min, self.max)

class Pstring(string, Parray):
    pass

class constant(domain):
    def __init__(self, value, type):
        self.value = value
        self.type = type
        if isinstance(type, number):
            type.max = type.min = value
        elif isinstance(type, (string, array)):
            type.max = type.min = len(value)
    def __repr__(self):
        return "<constant %r: %r>" % (self.value, self.type)

int1 = any_precision(2**7 - 1, -(2**7))
uint1 = byte = any_precision(2**8 - 1)
int2 = any_precision(2**15 - 1, -(2**15))
uint2 = any_precision(2**16 - 1)
int3 = any_precision(2**23 - 1, -(2**23))
uint3 = any_precision(2**24 - 1)
int4 = any_precision(2**31 - 1, -(2**31))
uint4 = any_precision(2**32 - 1)
