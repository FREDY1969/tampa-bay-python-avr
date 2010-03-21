# number.py


import math
from . import domain

def adj_binary_pt(i, old_pt, new_pt):
    r'''
        >>> adj_binary_pt(0x0A, 3, 3)
        10
        >>> adj_binary_pt(0x0A, 3, 1)
        3
        >>> adj_binary_pt(0x09, 3, 1)
        2
        >>> adj_binary_pt(0x0A, 3, 5)
        40
    '''
    delta_pt = new_pt - old_pt
    if delta_pt >= 0: return int(round(i * 2**delta_pt))
    delta_pt = -delta_pt
    return int(round(i / 2**delta_pt))

class fixed_precision:
    r'''
        >>> fixed_precision.from_str('0')
        0
        >>> fixed_precision.from_str('123')
        123
        >>> fixed_precision.from_str('123.23')
        123.23~4
        >>> fixed_precision.from_str('123.23~1')
        123.227~8
    '''
    def __init__(self, i, binary_pt):
        self.i = i
        self.binary_pt = binary_pt
    @classmethod
    def from_str(cls, str, base = 10):
        if '~' not in str:
            if '.' not in str:
                n = int(str, base)
                precision = 0.5
                decimal_pt = 0
            else:
                dot = str.index('.')
                i = int(str[:dot], base)
                n = int(str[dot+1:], base)
                decimal_pt = len(str) - dot - 1
                n += i * base**decimal_pt
                precision = 0.5
        else:
            tilde = str.index('~')
            assert tilde + 1 < len(str), \
                   "missing precision after '~' in approx number"
            if '.' not in str:
                n = int(str[:tilde], base)
                precision = float(int(str[tilde + 1:], base))
                decimal_pt = -(len(str) - tilde - 2)
                n *= base**-decimal_pt
                precision *= base**decimal_pt
            else:
                dot = str.index('.')
                assert dot < tilde, "'.' after '~' in approx number"
                i = int(str[:dot], base)
                n = int(str[dot+1:tilde], base)
                decimal_pt = tilde - dot - 1
                n += i * base**decimal_pt
                precision = float(int(str[tilde + 1:], base))
                precision /= base**(len(str) - tilde - 2)
        binary_pt = int(math.ceil(math.log(base, 2)*decimal_pt
                                    - math.log(precision, 2)))
        i = int(round(float(n) * float(2**binary_pt) / base**decimal_pt))
        return cls(i, binary_pt)
    def __repr__(self):
        # print "self.i", self.i, "self.binary_pt", self.binary_pt
        if self.binary_pt == 1 and (self.i & 1) == 0:
            return repr(self.i >> 1)
        if self.binary_pt < 0:
            return "{!r}~{!r}".format(self.i, 2**-(self.binary_pt - 1))
        if self.binary_pt == 0:
            return "{!r}".format(self.i)
        # 2**self.binary_pt = 10**decimal_pt / precision
        decimal_pt = int(math.ceil(self.binary_pt / math.log(10, 2)))
        n = self.i * 2**-self.binary_pt
        n1 = round(n, decimal_pt)
        precision = int(round(10.0**decimal_pt / 2**self.binary_pt))
        return "{}~{!r}".format(n1, precision)
    def __neg__(self):
        return self.__class__(-self.i, self.binary_pt)
    def __add__(self, b):
        if isinstance(b, int):
            # we take these to be exact numbers
            return self.__class__(self.i + adj_binary_pt(b, 0, self.binary_pt),
                                  self.binary_pt)
        elif isinstance(b, any_precision):
            return self.__class__(self.i + b.as_precision(self.binary_pt),
                                  self.binary_pt)
        elif isinstance(b, fixed_precision):
            if self.binary_pt == b.binary_pt:
                return self.__class__(self.i + b.i, self.binary_pt)
            if self.binary_pt > b.binary_pt:
                my_i = adj_binary_pt(self.i, self.binary_pt, b.binary_pt)
                return self.__class__(my_i + b.i, b.binary_pt)
            b_i = adj_binary_pt(b.i, b.binary_pt, self.binary_pt)
            return self.__class__(self.i + b_i, self.binary_pt)
        else:
            raise TypeError("can not add {} and {}"
                              .format(self.__class__.__name__,
                                      b.__class__.__name__))
    def __radd__(self, b):
        return self + b
    def __sub__(self, b):
        if isinstance(b, int):
            # we take these to be exact numbers
            return self.__class__(self.i + adj_binary_pt(b, 0, self.binary_pt),
                                  self.binary_pt)
        elif isinstance(b, any_precision):
            return self.__class__(self.i + b.as_precision(self.binary_pt),
                                  self.binary_pt)
        elif isinstance(b, fixed_precision):
            if self.binary_pt == b.binary_pt:
                return self.__class__(self.i + b.i, self.binary_pt)
            if self.binary_pt > b.binary_pt:
                my_i = adj_binary_pt(self.i, self.binary_pt, b.binary_pt)
                return self.__class__(my_i + b.i, b.binary_pt)
            b_i = adj_binary_pt(b.i, b.binary_pt, self.binary_pt)
            return self.__class__(self.i + b_i, self.binary_pt)
        else:
            raise TypeError("can not add {} and {}"
                              .format(self.__class__.__name__,
                                      b.__class__.__name__))
    def __rsub__(self, b):
        return -(self - b)

    def __mul__(self, b):
        # d(a*x)/dx = a
        if isinstance(b, int):
            # we take these to be exact numbers
            binary_pt = -int(math.floor(math.log(b, 2) - self.binary_pt))
            return self.__class__(adj_binary_pt(self.i * b, self.binary_pt,
                                                            binary_pt),
                                  binary_pt)
        elif isinstance(b, any_precision):
            binary_pt = -int(math.ceil(math.log(b, 2) - self.binary_pt))
            # math.log(self.i, 2) / self.binary_pt - b_pt > binary_pt
            # math.log(self.i, 2) / self.binary_pt - binary_pt > b_pt
            b_pt = -int(math.ceil(math.log(self.i, 2) / self.binary_pt + \
                                    binary_pt))
            return self.__class__(adj_binary_pt(self.i * b.as_precision(b_pt),
                                                self.binary_pt + b_pt,
                                                binary_pt),
                                  binary_pt)
        elif isinstance(b, fixed_precision):
            my_log = math.log(self.i, 2) / self.binary_pt
            b_log = math.log(b.i, 2) / b.binary_pt
            binary_pt = -int(math.ceil(max(my_log - b.binary_pt,
                                           b_log - self.binary_pt)))
            return self.__class__(adj_binary_pt(self.i * b.i,
                                                self.binary_pt + b.binary_pt,
                                                binary_pt),
                                  binary_pt)
        else:
            raise TypeError("can not multiply {} from {}"
                              .format(self.__class__.__name__,
                                      b.__class__.__name__))
    def __rmul__(self, b):
        return self * b

    def __div__(self, b):
        # d(a/x)/dx = -a/x**2
        # d(x/a)/dx = 1/a
        if isinstance(b, int):
            # we take these to be exact numbers
            binary_pt = -int(math.floor(-math.log(b, 2) - self.binary_pt))
            return self.__class__(adj_binary_pt(self.i / b, self.binary_pt,
                                                            binary_pt),
                                  binary_pt)
        elif isinstance(b, any_precision):
            binary_pt = -int(math.ceil(-math.log(b, 2) - self.binary_pt))
            # math.log(self.i, 2) / self.binary_pt - 2*b_pt - self.binary_pt
            #   > binary_pt
            # math.log(self.i, 2) / self.binary_pt - binary_pt - self.binary_pt
            #   > 2*b_pt
            b_pt = -(int(math.ceil(math.log(self.i, 2) / self.binary_pt - \
                                   binary_pt - self.binary_pt)) - 1)
            return self.__class__(adj_binary_pt(self.i / b.as_precision(b_pt),
                                                self.binary_pt - b_pt,
                                                binary_pt),
                                  binary_pt)
        elif isinstance(b, fixed_precision):
            my_log = math.log(self.i, 2) / self.binary_pt
            b_log = math.log(b.i, 2) / b.binary_pt
            binary_pt = -int(math.ceil(max(-self.binary_pt - b_log,
                                           my_log - 2*b_log - b.binary_pt)))
            return self.__class__(adj_binary_pt(self.i / b.i,
                                                self.binary_pt - b.binary_pt,
                                                binary_pt),
                                  binary_pt)
        else:
            raise TypeError("can not divide {} by {}"
                              .format(self.__class__.__name__,
                                      b.__class__.__name__))

    def __rdiv__(self, b):
        # d(a/x)/dx = -a/x**2
        # d(x/a)/dx = 1/a
        my_log = math.log(self.i, 2) / self.binary_pt
        if isinstance(b, int):
            # we take these to be exact numbers
            binary_pt = -int(math.floor(math.log(b, 2) - 2*my_log - 
                                          self.binary_pt))
            return self.__class__(adj_binary_pt(b / self.i, -self.binary_pt,
                                                            binary_pt),
                                  binary_pt)
        elif isinstance(b, any_precision):
            binary_pt = -int(math.floor(math.log(b, 2) - 2*my_log - 
                                          self.binary_pt))
            # -math.log(self.i, 2) / self.binary_pt - b_pt > binary_pt
            # -math.log(self.i, 2) / self.binary_pt - binary_pt > b_pt
            b_pt = -int(math.ceil(-math.log(self.i, 2) / self.binary_pt - \
                                    binary_pt))
            return self.__class__(adj_binary_pt(b.as_precision(b_pt) / self.i,
                                                b_pt - self.binary_pt,
                                                binary_pt),
                                  binary_pt)
        elif isinstance(b, fixed_precision):
            b_log = math.log(b.i, 2) / b.binary_pt
            binary_pt = -int(math.ceil(max(b_log - 2*my_log - self.binary_pt,
                                           -my_log - b.binary_pt)))
            return self.__class__(adj_binary_pt(b.i / self.i,
                                                b.binary_pt - self.binary_pt,
                                                binary_pt),
                                  binary_pt)
        else:
            raise TypeError("can not divide {} by {}"
                              .format(b.__class__.__name__,
                                      self.__class__.__name__))

    def to_domain(self):
        return domain.constant(self,
                               domain.fixed_precision(self, self,
                                                      self.binary_pt,
                                                      self.binary_pt))

class any_precision:
    r'''
        >>> any_precision.from_str('0/')
        0/
        >>> any_precision.from_str('123/')
        123/
        >>> any_precision.from_str('123.23/')
        123.23/
        >>> any_precision.from_str('123.23/64')
        123.23/64
    '''
    def __init__(self, numerator, denominator = 1):
        self.numerator = numerator
        self.denominator = denominator
    @classmethod
    def from_str(cls, str, base = 10):
        assert '/' in str, "missing '/' in exact number"
        slash = str.index('/')
        if '.' not in str:
            numerator = int(str[:slash], base)
            if slash + 1 == len(str):
                denominator = 1
            else:
                denominator = int(str[slash + 1:], base)
        else:
            dot = str.index('.')
            assert dot < slash, "'.' after '/' in exact number"
            i = int(str[:dot], base)
            n = int(str[dot+1:slash], base)
            if slash + 1 == len(str):
                denominator = base**(slash - dot - 1)
            else:
                denominator = int(str[slash + 1:], base)
            numerator = i * denominator + n
        return cls(numerator, denominator)
    def __repr__(self):
        i = self.numerator // self.denominator
        if i == 0:
            if self.numerator == 0: return "0/"
            return "{!r}/{!r}".format(self.numerator, self.denominator)
        r = self.numerator - self.denominator * i
        if r == 0:
            return "{!r}/".format(i)
        l = math.log10(self.denominator)
        if abs(l - round(l)) < 1e-9:
            rs = "{!r}".format(r)
            return "{!r}.{}{}/".format(i, '0' * (int(round(l)) - len(rs)), rs)
        return "{!r}.{!r}/{!r}".format(i, r, self.denominator)
    def __float__(self):
        return float(self.numerator) / float(self.denominator)
    def to_domain(self):
        return domain.constant(self, domain.any_precision(self, self))

