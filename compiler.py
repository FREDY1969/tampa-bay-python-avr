# compiler.py

'''
    The compiler converts to reverse polish by providing a stack of words.
'''

import word
import domain
import number

class compiler(object):
    word_compiler = None
    def __init__(self, infile):
        self.tokenizer = tokenizer(infile, self)
        self.token_iter = iter(self.tokenizer)
        self.saved_token = None
    def __contains__(self, key):
        if self.word_compiler:
            return key in self.word_compiler
        return key in word.Words
    def __getitem__(self, key):
        if self.word_compiler:
            return self.word_compiler[key]
        return word.Words[key]
    def next(self):
        if not self.saved_token:
            return self.token_iter.next()
        ans = self.saved_token
        self.saved_token = None
        return ans
    def unnext(self, token, value):
        assert not self.saved_token
        self.saved_token = token, value
    def syntaxerror_params(self):
        return self.tokenizer.syntaxerror_params()
    def get_name(self):
        token, name = self.token_iter.next()
        if token != 'NAME':
            raise SyntaxError("NAME expected", self.syntaxerror_params())
        return name
    def compile(self):
        for token, word in self.token_iter:
            if token != 'WORD':
                raise SyntaxError("illegal declaration",
                                  self.syntaxerror_params())
            word.compile_declaration(self)

class compile_word(object):
    def __init__(self, compiler):
        self.compiler = compiler
        self.locals = {} # {name: offset} -- args have an offset < 0, locals > 0
        self.next_local_offset = 2
        self.next_arg_offset = 0
        self.flash_start = word.Flash_end
    def __contains__(self, key):
        return key in self.locals or key in word.Words
    def __getitem__(self, key):
        if key in self.locals: return self.locals[key]
        return word.Words[key]
    def addr(self): return word.Flash_end
    def patch(self, addr_list, dest_addr):
        for addr in addr_list:
            Flash[addr] = dest_addr & 0xff
            Flash[addr + 1] = dest_addr >> 8
    def push(self, x):
        if Flash_end >= 15 * 1024:
            raise MemoryError("Out of Flash memory")
        word.Flash[Flash_end] = x
        Flash_end += x
    def push2(self, x):
        self.push(x & 0xff)
        self.push(x >> 8)
    def compile_expr(self, rprec = 0):
        r'''
            Returns the domain.  Literals are not pushed into code (i.e., a
            'lit' word is not created).
        '''
        token, value = self.compiler.next()
        if token == 'NUMBER':
            ans = value
        elif token == 'WORD':
            ans = value.compile_value(self)
        elif token == '(':
            ans = self.compile_expr(0)
            token, value = self.compiler.next()
            if token != ')':
                raise SyntaxError("expected ')', got %s" % token,
                                  self.syntaxerror_params())
        else:
            raise SyntaxError("expected expression, got %s" % token,
                              self.syntaxerror_params())
        while True:
            token, value = self.compiler.next()
            if token != 'WORD' or not value.left_prec < rprec:
                self.compiler.unnext(token, value)
                break
            ans = value.compile_value(self, ans)
        return ans
    def compile_params(self, word):
        r'''
            Returns the number of parameters passed.
        '''
        token, value = self.compiler.next()
        if token == 'START_PARAMS':
            end_token = (')',)
            token, value = self.compiler.next()
        else:
            end_token = (':', 'NEWLINE', 'EOF')
        i = 0
        while token not in end_token:
            self.compiler.unnext(token, value)
            self.compile_expr().coerce(word.arg_domains[i])
            token, value = self.compiler.next()
            i += 1
        if token != ')':
            self.compiler.unnext(token, value)
        return i
    def series(self):
        # FIX
        pass

class tokenizer(object):
    def __init__(self, infile, dictionary):
        self.infile = infile
        self.dictionary = dictionary
    def syntaxerror_params(self):
        return self.infile.name, self.lineno, self.charnum, self.line
    def __iter__(self):
        r'''
        yields token, value
        '''
        self.lineno = 1
        indent = 0
        indent_stack = [0]
        nl_escaped = False
        nested_parens = 0
        for line in self.infile:
            if '#' in line:
                i = line.index('#')
                if i == 0 or line[i - 1].isspace():
                    line = line[:i]
            self.line = line = line.rstrip()
            if not line: continue
            self.charpos, self.charnum = get_indent(line)
            line = line.lstrip()
            if not nl_escaped and not nested_parens:
                if self.charpos > indent_stack[-1]:
                    yield 'INDENT', None
                    indent_stack.append(self.charpos)
                else:
                    while self.charpos < indent_stack[-1]:
                        yield 'DEINDENT', None
                        del indent_stack[-1]
                if self.charpos != indent_stack[-1]:
                    raise SyntaxError("illegal de-indent, "
                                        "doesn't match prior indent",
                                      self.syntaxerror_params())
            nl_escaped = False
            intoken = False
            base = 0
            for i, c in enumerate(line):
                if c == ' ':
                    if intoken:
                        yield self.end_token(token, base)
                        intoken = False
                    self.charpos += 1
                    self.charnum += 1
                elif c == '\t':
                    raise SyntaxError("tabs not allowed",
                                      self.syntaxerror_params())
                elif c in '()[]':
                    if intoken:
                        yield self.end_token(token, base)
                        intoken = False
                        if c == '(':
                            yield 'START_PARAMS', None
                        else:
                            yield c, None
                    else:
                        yield c, None
                    self.charpos += 1
                    self.charnum += 1
                    if c in '([': nested_parens += 1
                    elif nested_parens: nested_parens -= 1
                elif intoken:
                    token += c
                    if token == '0x': base = 16
                    elif not c.isdigit() and c not in '.~/' and \
                         (base == 10 or \
                          base == 16 and not c.lower() in 'abcdef'):
                        base = 0
                    self.charpos += 1
                    self.charnum += 1
                elif c == '#':
                    raise SyntaxError("'#' not preceeded by space",
                                      self.syntaxerror_params())
                elif c == '-':
                    if i + 1 < len(line) and not line[i + 1].isspace():
                        c = 'negate'
                    if c in self.dictionary:
                        yield 'WORD', self.dictionary[c]
                    else:
                        yield 'NAME', c
                    self.charpos += 1
                    self.charnum += 1
                elif c == '\\': # Line continuation must have space before.
                    if i + 1 >= len(line):
                        nl_escaped = True
                    # else ignore it ...
                else:
                    token = c
                    base = 10 if c.isdigit() else 0
                    self.charpos += 1
                    self.charnum += 1
                    intoken = True
            if intoken:
                yield self.end_token(token, base)
            if not nl_escaped: yield 'NEWLINE', None
        yield 'EOF', None
    def end_token(self, token, base):
        dot_split = token.split('.')
        if base and len(dot_split) < 3 and '~' not in dot_split[0] and \
           '/' not in dot_split[0] and \
           (len(dot_split) < 2 or 
            dot_split[1].count('~') + dot_split[1].count('/') < 2):
            if '/' in token:
                return 'NUMBER', number.any_precision.from_str(token, base) \
                                       .to_domain()
            return 'NUMBER', number.fixed_precision.from_str(token, base) \
                                   .to_domain()
        if token in self.dictionary:
            return 'WORD', self.dictionary[token]
        return 'NAME', token

def get_indent(line):
    r'''
        >>> get_indent('hi mom')
        (1, 1)
        >>> get_indent('  hi mom')
        (3, 3)
        >>> get_indent('\thi mom')
        (9, 2)
        >>> get_indent('       \thi mom')
        (9, 9)
        >>> get_indent('        \thi mom')
        (17, 10)
    '''
    charpos = 1
    for i, c in enumerate(line):
        if c == '\t':
            charpos = ((charpos + 7) & ~7) + 1
        elif c == ' ':
            charpos += 1
        else:
            break
    return charpos, i + 1
