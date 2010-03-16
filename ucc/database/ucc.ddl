-- ucc.ddl

-- The schema for the ast database.

---------------------------------------------------------------------------
-- These are the tables populated by the parse_file method.
---------------------------------------------------------------------------
create table symbol_table (
    id integer not null primary key,
    context integer references symbol_table(id),
    label varchar(255) not null collate nocase,
    kind varchar(255) not null,
        -- e.g.:
           -- 'function'        -- address
           -- 'task'            -- address
           -- 'const'           -- reg_class, register or address
           -- 'var'             -- reg_class, register or address
           -- 'parameter'       -- int1 is parameter number, param_register, 
                                -- reg_class, register or address
           -- 'return'          -- reg_class, register
           -- 'label'           -- address
           -- 'placeholder'     -- temp kind, to be updated later to real kind.
    source_filename varchar(4096),      -- full path to source file
    type_id int references type(id),
    int1 int,
    param_register varchar(255),
    address int,
    reg_class int,
    register varchar(255),
    flash_size int,
    ram_size int,
    far_size int,
    clock_cycles int,
    side_effects bool default 0,        -- only for functions/tasks
    suspends bool default 0,            -- only for functions/tasks
    unique (label, context)
);

create table type (
    -- Describes what is known about a value at compile time.

    id integer not null primary key,
    kind varchar(255) not null,
        -- 'int' (min_value, max_value)
        -- 'fixedpt' (min_value, max_value, binary_pt)
        -- 'array' (min_value, max_value of array size, element_type)
        -- 'pointer' (memory, element_type)
        -- 'record' (see sub_element table)
        -- 'function' (element_type is return type,
        --             min_value, max_value of arguments,
        --             sub_element table is arg types)
    min_value int,
    max_value int,
    binary_pt int,              -- Number of bits _before_ the binary point
                                --   so that a number taken as an int *
                                --   2**binary_pt is the desired value.
                                -- For example, 1/4 would be 1 with a
                                --   binary_pt of -2.
    memory varchar(255),        -- only for pointers
        -- 'flash'
        -- 'eeprom'
        -- 'ram'
    element_type int references type(id)
);

create index numeric_type_index on type
    (kind, max_value, min_value, binary_pt);

create index compound_type_index on type
    (kind, element_type, max_value, min_value);

create table sub_element (
    parent_id int not null references type(id),
    element_order int not null,
    name varchar(255) not null,
    element_type int not null references type(id),
    primary key (parent_id, name),
    unique (parent_id, element_order)
);

create table ast (
    -- The Abstract Syntax Tree (AST).  See AbstractSyntaxTree page in google
    -- code project wiki.

    id integer not null primary key,
    word_symbol_id int not null references symbol_table(id),

    -- For macro expansions:
    --id_replaced int unique references ast(id),
    --root_id_replaced int references ast(id),
    --replacement_depth int,

    kind varchar(255),                         -- type of ast node
       -- possible values are:
          -- 'approx': int1 = number_as_integer, int2 = binary_pt
             -- actual number == int1 * 2^int2
          -- 'int': int1 = integer
          -- 'ratio': int1 = numerator, int2 = denominator
          -- 'string': str1 = string
          -- 'call': first arg = fn
          -- 'word': label = word label, symbol_id = symbol_id of word
          -- 'ioreg': label = ioreg name (e.g., 'io.portd')
          -- 'ioreg-bit': label = ioreg name (e.g., 'io.portd'), int1 = bit#
          -- 'no-op':
          -- 'label': label = label
          -- 'jump': label = target
          -- 'if-false': label = jump-false target, first arg is condition
          -- 'if-true': label = jump-true target, first arg is condition
          -- 'series': args are statements to splice in
          -- 'None': line, column info not set

    label varchar(255),                        -- word label
    symbol_id int references symbol_table(id),
    int1 int,
    int2 int,
    str1 varchar(2000),
    str2 varchar(2000),                        -- not used, but leaving it here
                                               -- for the moment...

    expect varchar(255),                       -- what's expected by the parent
       -- possible values are:
          -- 'statement'
          -- 'condition'
          -- 'value' (rvalue)
          -- 'lvalue'
          -- 'producer'
          -- 'start_stop'

    expected_type int references type(id),      -- maybe not needed?
    type_id int references type(id),

    -- ast argument nodes are linked to their parent nodes:
    parent_node int references ast(id),        -- null for top-level
    parent_arg_num int,
    arg_order int,                             -- for list arguments, else 0

    -- for nodes generated by the parser:
    line_start int,
    column_start int,
    line_end int,
    column_end int,

    --unique (root_id_replaced, replacement_depth),
    unique (parent_node, parent_arg_num, arg_order)
);

create index word_index on ast (symbol_id, kind, expect);

create index word_body_index on ast (word_symbol_id,
                                     parent_node, parent_arg_num, arg_order);


---------------------------------------------------------------------------
-- Needed to construct the next two tables
---------------------------------------------------------------------------
create table fn_calls (
    -- who calls who
    caller_id int not null references symbol_table(id),
    called_id int not null references symbol_table(id),
    depth int not null default 1,
    primary key (caller_id, called_id)
);

---------------------------------------------------------------------------
-- Needed to generate the intermediate code
---------------------------------------------------------------------------
create table fn_global_var_uses (
    -- the global variables used by a function (directly or indirectly)
    fn_id int not null references symbol_table(id),
    var_id int not null references symbol_table(id),
    sets bool not null,
    depth int not null default 0,
    primary key (fn_id, var_id, sets)
);

---------------------------------------------------------------------------
-- ucc.database.crud.gensym stores info here.
--
-- Nobody else knows about this...
---------------------------------------------------------------------------
create table gensym_indexes (
    prefix varchar(255) not null,
    last_used_index int not null
);


---------------------------------------------------------------------------
---------------------------------------------------------------------------
-- These are the tables for the intermediate code.
---------------------------------------------------------------------------
---------------------------------------------------------------------------
create table blocks (
    id integer not null primary key,
    name varchar(255) not null unique,               -- used as jump target
    word_symbol_id int not null references symbol_table(id),

    last_triple_id int references triples(id),  -- doesn't seem to be used...
    next varchar(255) references blocks(name),
    next_conditional varchar(255) references blocks(name)
);

create table block_successors (
    predecessor int not null references blocks(id),
    successor int not null references blocks(id),
    primary key (predecessor, successor)
);

create index block_successors_index
          on block_successors (successor, predecessor);

create table triples (
    id integer not null primary key,
    block_id int not null references blocks(id),
    operator varchar(255) not null,
       -- special values:
       --   'input'            -- string is port name
       --   'input-bit'        -- string is port name, int1 is bit#
       --   'output'           -- string is port name, int1 is triples id
       --   'output-bit-set'   -- string is port name, int1 is bit#
       --   'output-bit-clear' -- string is port name, int1 is bit#
       --   'global_addr'      -- int1 is symbol_table id
       --   'global'           -- int1 is symbol_table id
       --   'local_addr'       -- int1 is symbol_table id
       --   'local'            -- int1 is symbol_table id
       --   'int'              -- int1
       --   'ratio'            -- int1 is numerator, int2 is denominator
       --   'approx'           -- int1 * 2**int2
       --   'param'            -- int1 is which param, int2 is triples id,
                               -- call_triple_id is function call triple
       --   'call_direct'      -- int1 is symbol_table id
       --   'call_indirect'    -- int1 is triples id
       --   'return'           -- int1 is optional triples id
       --   'if_false'         -- int1 is triples id to cond, string is label
       --   'if_true'          -- int1 is triples id to cond, string is label
       -- else operator applies to int1 and int2 as triples ids
    int1 int,
    int2 int,
    call_triple_id int references triple(id),
    string varchar(32768),
    type_id int references type(id),
    reg_class int,
    register_est int,          -- Estimate of number of registers needed by
                               -- this node and all of it's decendants.
    reverse_children int,      -- If true, evaluate int2 operand first.
    order_in_block int,        -- order within block
    line_start int,
    column_start int,
    line_end int,
    column_end int
);

create table triple_labels (
    -- The symbols (if any) that each triple's result must be stored in.

    triple_id int not null references triples(id),
    symbol_id int not null references symbol_table(id),

    -- True if this is the last triple to set this symbol in this block.
    is_gen bool not null,

    primary key (triple_id, symbol_id)
);

create table gens (
    block_id int not null references blocks(id),
    symbol_id int not null references symbol_table(id),
    triple_id int not null references triples(id)
);

create table triple_order_constraints (
    predecessor int not null references triples(id),
    successor int not null references triples(id),
    primary key (predecessor, successor)
);

create index toc_successor_index
          on triple_order_constraints(successor, predecessor);

create table kills (
    block_id int not null references blocks(id),
    symbol_id int not null references symbol_table(id),
    primary key (block_id, symbol_id)
);

create table ins (
    block_id int not null references blocks(id),
    symbol_id int not null references symbol_table(id),
    triple_id int not null references triples(id),
    primary key (block_id, symbol_id, triple_id)
);

create table outs (
    block_id int not null references blocks(id),
    symbol_id int not null references symbol_table(id),
    triple_id int not null references triples(id),
    primary key (block_id, symbol_id, triple_id)
);


-----------------------------------------------------------------------------
-----------------------------------------------------------------------------
-- The tables that hold the assembler sources.
--
-- These are broken out by blocks to facilitate the assembler playing games
-- with the block ordering to maximize the use of smaller jmp and call insts.
-----------------------------------------------------------------------------
-----------------------------------------------------------------------------
create table assembler_blocks (
    id integer not null primary key,
    section varchar(255) not null,
        -- 'code'
        -- 'data'
        -- 'bss'
        -- 'eeprom' (this probably gets broken out into several tables)
    label varchar(255) unique,
    next_label varchar(255),
    word_symbol_id int not null references symbol_table(id),
    address int,
    min_length int,
    max_length int,
    min_clock_cycles int,
    max_clock_cycles int
);

create table assembler_code (
    id integer not null primary key,
    block_id int not null references assembler_blocks(id),
    inst_order int not null,
    label varchar(255) unique,
    opcode varchar(255),
        -- special opcodes:
           -- 'bytes', operand1 has data value in hex form (no initial '0x')
              -- or in 'string' or "string" form (with standard python escapes).
           -- 'int8', operand1 has data value in string form
              -- (may have '0x' prefix)
           -- 'int16', operand1 has data value in string form
              -- (may have '0x' prefix)
           -- 'int32', operand1 has data value in string form
              -- (may have '0x' prefix)
           -- 'zeroes', operand1 has data length in string form.
    operand1 varchar(255),
    operand2 varchar(255),
    min_length int not null,       -- in bytes
    max_length int not null,       -- in bytes
    min_clocks int,                -- for machine instructions (code section)
    max_clocks int,                -- for machine instructions (code section)
    end bool,                      -- 1 if this inst doesn't fall through
    line_start int,
    column_start int,
    line_end int,
    column_end int,

    unique (block_id, inst_order)
);

