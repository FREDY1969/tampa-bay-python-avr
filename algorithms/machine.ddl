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
    v int not null references vertex(id)
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
    -- assigned to.  So the tree represents a subset 
    --
    -- Referred to by reg_class.

    id integer not null primary key,
    parent int references vertex(id)
);

create table v_classes (
    -- All reg_classes in v and v's children.

    v int not null references vertex(id),
    C int not null references reg_class(id),
    unique (v, C)
);

create table bound (
    -- Max #registers from reg_class N that can be trashed by assigning to all
    -- registers in reg_classes in vertex v and v's children.

    N int not null references reg_class(id),
    v int not null references vertex(id),
    value int not null,
    unique (N, v)
);
