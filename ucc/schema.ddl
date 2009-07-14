-- schema.ddl

create table enum (
    -- One-size-fits-all enum table...
    --
    -- To get the list of choices for enum 'foo':
    --     select enum_id, id, name from enum 
    --     where enum_id = (select id from enum
    --                      where enum_id = 1 and name = 'foo')
    --     order by id
    --

    id integer not null primary key,
    enum_id int not null references enum(id),
    name varchar(255) not null,
    unique (enum_id, name)
);


create table node (
    -- The Abstract Syntax Tree (AST).  See AbstractSyntaxTree page in google
    -- code project wiki.

    id integer not null primary key,
    id_replaced int references node(id),            -- For macro expansions.
    kind int not null,                              -- From enum 'node_kind'.
    word_id int references word(id),                -- Used by definition, word,
                                                    -- and byte code.
    int_literal int,                                -- Used by literal and
                                                    -- byte codes that have a
                                                    -- numeric argument.
    str_literal varchar(1000),                      -- Used by literal,
                                                    -- byte codes that have a
                                                    -- label argument, and
                                                    -- assembler.
    line_no int,
    column_no int,
    parent_node int references node(id),
    parent_position int
);

