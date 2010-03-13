# number.py



import numbers
import math

class fraction(object):
    r'''
        >>> fraction('-1.3/4')
        fraction(-7, 4)
        >>> fraction('1.3/4')
        fraction(7, 4)
        >>> fraction('3/4')
        fraction(3, 4)
        >>> fraction('-3/4')
        fraction(-3, 4)
        >>> fraction('-0xb/10')
        fraction(-11, 16)
        >>> fraction('0xA.b/10')
        fraction(171, 16)
    '''
    def __init__(self, s):
        sign = 1
        if s.startswith('-'):
            sign = -1
            s = s[1:]
        base = 10
        s = s.lower()
        if s.startswith('0x'):
            base = 16
            s = s[2:]
        s2 = s.split('.')
        self.numerator, self.denominator = [int(s, base) for s in s2[-1].split('/')]
        if len(s2) > 1: self.numerator += int(s2[0], base) * self.denominator
        self.numerator *= sign
    def __repr__(self):
        return "fraction(%d, %d)" % (self.numerator, self.denominator)
    def at_precision(self, n):
        return int(round(self * 2**n))

class approx(object):
    r'''
        >>> approx('123.5')
        approx(1976, -4)
        >>> approx('-123.5')
        approx(-1976, -4)
        >>> approx('0x7b.8')
        approx(1976, -4)
        >>> approx('-0x7B.8')
        approx(-1976, -4)
    '''
    def __init__(self, s):
        sign = 1
        if s.startswith('-'):
            sign = -1
            s = s[1:]
        base = 10
        s = s.lower()
        if s.startswith('0x'):
            base = 16
            s = s[2:]
        self.int, self.exp = parse_approx(s, base)
        self.int *= sign
    def __repr__(self):
        return "approx(%d, %d)" % (self.int, self.exp)
    def at_precision(self, n):
        if n == self.exp: return self.int
        if n < self.exp:
            return int(round(self.int / 2**(self.exp - n)))
        return self.int * 2**(n - self.exp)
    def int_exp(self):
        return self.int, self.exp

def parse_approx(s, base = 10):
    r'''Return the approx value for s as (integer, binary_pt).

    The format for s is: digit* .digit* ~digit e[+-]?digit*
    Note that this does not accept negative numbers.

    >>> parse_approx('123.')
    (123, 0)
    >>> parse_approx('123~1')
    (123, 0)
    >>> parse_approx('122~1')
    (61, 1)
    >>> parse_approx('123.5')
    (1976, -4)
    >>> parse_approx('123.5~1')
    (988, -3)
    >>> parse_approx('123~1e1')
    (77, 4)
    >>> parse_approx('123e1')
    (308, 2)
    >>> parse_approx('123~1e-1')
    (197, -4)
    >>> parse_approx('123e-1')
    (197, -4)
    '''
    dot = s.find('.')
    tilde = s.find('~')
    e = s.find('e' if base == 10 else 'x')
    if e < 0:
        exp = 0
        e = len(s)
    else:
        exp = int(s[e + 1:])
    if tilde < 0:
        prec = base // 2
        prec_place = 1
        tilde = e
    else:
        prec = int(s[tilde + 1:e], base)
        prec_place = 0
    if dot < 0:
        decimal_places = 0
        n = int(s[:tilde], base)
    else:
        decimal_places = tilde - dot - 1
        if dot > 0:
            n = int(s[:dot], base) * base**decimal_places
        else:
            n = 0
        if decimal_places:
            n += int(s[dot + 1:tilde], base)

    number = n * base**(exp - decimal_places)
    precision = prec / base**(decimal_places + prec_place - exp)

    #print "n", n, "decimal_places", decimal_places, \
    #      "prec", prec, "prec_place", prec_place, "exp", exp
    #
    #print "number", number
    #print "precision", precision

    # We want the greatest integer binary_pt such that:
    #
    #    (i - 0.5) * 2**binary_pt >= number - precision
    #    (i + 0.5) * 2**binary_pt <= number + precision
    #
    # for some integer, i.
    #
    # This can not be solved directly.
    #
    # So we'll take an iterative approach starting with:
    #
    #    2**binary_pt * 0.5 == precision
    #
    # Solving for binary_pt:
    #
    #    binary_pt = log2(2 * precision)
    #    binary_pt = log2(precision) + 1

    target = math.log(precision) / math.log(2) + 1
    binary_pt = int(math.ceil(target))
    smallest_reject = None
    largest_ok = None

    while smallest_reject is None or largest_ok is None:
        i = int(round(number / 2**binary_pt))
        if (i - 0.5) * 2**binary_pt >= number - precision and \
           (i + 0.5) * 2**binary_pt <= number + precision:
            largest_ok = i, binary_pt
            binary_pt += 1
        else:
            smallest_reject = binary_pt
            binary_pt -= 1
    return largest_ok

