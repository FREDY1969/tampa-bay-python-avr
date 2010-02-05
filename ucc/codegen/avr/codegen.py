# codegen.py

from ucc.database import assembler, block, crud, symbol_table, triple

def gen_assembler():
    for fun_id, fun_label, fun_kind \
     in crud.read_as_tuples('symbol_table', 'id', 'label', 'kind',
                            kind=('function', 'task')):
        with crud.db_transaction():
            gen_fun(fun_id, fun_label, fun_kind)

def gen_fun(fun_id, fun_label, fun_kind):
    if fun_kind == 'function': far_size = 2
    else: far_size = 4
    prolog = assembler.block(fun_id, 'flash', fun_label)
    prolog.append_inst('push', 'r29')
    prolog.append_inst('push', 'r28')
    for id, kind, param_num \
     in crud.read_as_tuples('symbol_table', 'id', 'kind', 'int1',
                            context=fun_id,
                            order_by=('kind', 'desc', 'int1')):
        sym = symbol_table.get_by_id(id)
        far_size += 2
        sym.address = -far_size
        if fun_kind == 'task':
            sym.ram_size = 2
        if kind == 'parameter':
            prolog.append_inst('push', 'r%d' % (2 * param_num + 1))
            prolog.append_inst('push', 'r%d' % (2 * param_num))
    for id, name, next, next_conditional \
     in crud.read_as_tuples('blocks', 'id', 'name', 'next',
                            'next_conditional',
                            word_symbol_id=fun_id,
                            order_by=('id',)):
        asm_block = assembler.block(fun_id, 'flash', name)
        if next: asm_block.next_label(next)
        for what, should, this, be \
         in crud.read_as_tuples('triples',
                                block_id=id,
                                # FIX: finish...
                               ): pass

