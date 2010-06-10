-- machine.ddl

create table register (
    -- one row per register

    name varchar(20) not null primary key
);

create table alias (
    -- Aliases for register r1 are r2.
    --
    -- This means that assigning something to r1 also trashes r2.
    --
    -- These are generally, though not necessarily, symmetrical.
    --
    -- A register is always an alias of itself (since assigning to r1 always
    -- trashes r1).

    r1 varchar(20) not null references register(name),
    r2 varchar(20) not null references register(name),
    unique (r1, r2)
);

create table reg_class (
    -- A class of registers.  Each instruction operand requires a register from
    -- one of these classes.
    --
    -- Each reg_class is a set of registers.  (see reg_in_class).

    id integer not null primary key,
    name varchar(20) not null unique,
    num_registers int not null default 1,       -- ie, register width
    v int references vertex(id)
);

create table reg_in_class (
    -- The list of registers in each reg_class.
    --
    -- A single register may be the member of multiple reg_classes.

    reg_class int not null references reg_class(id),
    reg varchar(20) not null references register(name),
    unique (reg_class, reg)
);

create index reg_in_class_idx on reg_in_class (reg, reg_class);

-- is this actually needed?
create table class_alias (
    -- All of the aliases for all of the registers in each reg_class.

    reg_class int not null references reg_class(id),
    reg varchar(20) not null references register(name),
    unique (reg_class, reg)
);

create table worst (
    -- The worst (max) number of registers in reg_class N that can be trashed
    -- by using a single register in reg_class C.
    --
    -- Note that if C is a class of register pairs, and N is a class of single
    -- registers; using a single register in C could trash two registers in N.

    N int not null references reg_class(id),
    C int not null references reg_class(id),
    value int not null,
    unique (N, C)
);

create index worst_idx on worst (C, N);

create table vertex (
    -- Tree (root has NULL parent) of reg_classes.  Each node represents a set
    -- of registers, and each child is a subset of it's parent.
    --
    -- Each reg_class is assigned to one node in this tree.  If the aliases
    -- for two reg_classes are the same, they are assigned to the same node.
    -- Otherwise, if the aliases for reg_class X are a subset of the aliases
    -- for reg_class Y, then X is assigned to a child of the node Y is
    -- assigned to.  So the tree represents the subset relationship amoung
    -- reg_classes.  (There is an assumption that no two register classes
    -- intersect without one of them being a subset of the other).
    --
    -- Referred to by reg_class.

    id integer not null primary key,
    bit_mask int,       -- this vertex's bit in the bit map.
    vertex_set int,     -- bit map of included vertexes.
    parent int references vertex(id),
    height int          -- from bottom, starting at 1
);

create table v_classes (
    -- All reg_classes in v and v's children.

    v int not null references vertex(id),
    C int not null references reg_class(id),
    unique (v, C)
);

create table reg_class_subsets (
    rc1 int not null references reg_class(id),
    rc2 int not null references reg_class(id),
    subset int not null references reg_class(id),
    primary key (rc1, rc2)
);

create table bound (
    -- Max #registers from reg_class N that can be trashed by assigning to all
    -- registers in reg_classes in vertex v and v's children.

    N int not null references reg_class(id),
    v int not null references vertex(id),
    value int not null,
    unique (N, v)
);

create table operator_info (
    operator varchar(255) not null primary key,
    num_extra_regs int not null
);

create table code_seq_by_processor (
    processor varchar(255) not null,
    code_seq_id int not null references code_seq(id),
    primary key (processor, code_seq_id)
);

create table code_seq (
    id integer not null primary key,
    preference int not null,
    operator varchar(255) not null,
    output_reg_class int references reg_class(id),
    num_output int,
    from_param_num int
);

create unique index pattern_idx on code_seq(operator, preference, id);

create table code_seq_parameter (
    code_seq_id int not null references code_seq(id),
    parameter_num int not null,

    -- pattern conditions (these all default to null == "don't care"):
    opcode varchar(255),
    const_min int,
    const_max int,
    last_use bool,

    -- parameter requirements:
    reg_class int references reg_class(id),
    num_registers int,
    trashes bool default 0,
    delink bool default 0,

    primary key (code_seq_id, parameter_num)
);

create table reg_requirements (
    code_seq_id int not null references code_seq(id),
    reg_class int not null references reg_class(id),
    num_needed int not null,
    primary key (code_seq_id, reg_class)
);

create table code (
    code_seq_id int not null references code_seq(id),
    inst_order int not null,
    label varchar(255),
    opcode varchar(255) not null,
    operand1 varchar(255),
    operand2 varchar(255),
    primary key (code_seq_id, inst_order)
);

