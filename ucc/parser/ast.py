# ast.py

'''Internal AST representation (prior to going to database).

This is the AST representation created by the parser.  At the end of the
parse, this structure is stored into the database and then discarded.
'''

from ucc.parser import scanner

class ast(object):
    attr_cols = (
        'kind', 'expect', 'word_id', 'int1', 'int2', 'str',
        'line_start', 'column_start', 'line_end', 'column_end',
    )

    arg_cols = (
        'parent_node', 'parent_arg_num', 'arg_position',
    )

    sql_call = "insert into ast (%s) values (%s)" % \
                 (', '.join(attr_cols + arg_cols),
                  ', '.join('?' * (len(attr_cols) + len(arg_cols))))

    # default attribute values:
    kind = 'fn_call'
    expect = 'value'
    word_id = int1 = int2 = str = None

    def __init__(self, tok_start = None, tok_end = None, *args, **kws):
        self.args = args
        for name, value in kws:
            setattr(self, name, value)

        if tok_start is None:
            tok_start = fn
        if tok_end is None:
            tok_end = tok_start
        self.line_start, self.column_start = get_lineno_column(tok_start)
        self.line_end, self.column_end = get_lineno_column(tok_end)

    def save(self, db_cur,
             parent = None, parent_arg_num = None, arg_position = None):
        db_cur.execute(sql_call,
                       map(self.__getattr__, self.attr_cols) +
                         [parent, parent_arg_num, arg_position])
        my_id = db_cur.lastrowid
        for arg_num, arg in enumerate(self.args):
            if isinstance(arg, ast):
                arg.save(db_cur, my_id, arg_num, 0)
            else:
                for position, x in enumerate(arg):
                    x.save(db_cur, my_id, arg_num, position)

def insert(ast, db_conn):
    db_cur = db_conn.cursor()
    try:
        ast.save(db_cur)
        db_conn.commit()
    except Exception:
        db_conn.rollback()
        raise

def get_lineno_column(tok):
    return tok.lineno, scanner.get_col_line(tok.lexer.lexdata, tok.lexpos)[0]

