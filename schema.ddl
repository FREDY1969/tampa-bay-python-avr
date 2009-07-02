-- schema.ddl


create table naming_authority (
    -- Initially just one row for our group, auth_id = 1.  Each auth_id is
    -- unique world-wide.
    -- Each naming_authority may assign up to 99 developers, which have an id
    -- of:
    --     auth_id * 100 + 1:99.

    auth_id int not null primary key,
    name varchar(255) not null,
    email_name varchar(255) not null,
    email_url varchar(255) not null,
    next_dev_id int not null default 1,
    unique (name)
);


create table developer (
    -- The developer id is guaranteed world-wide unique by the naming_authority
    -- (see above).  Bruce is the first developer, or id 101 (dev 1 for
    -- auth_id 1).

    id int not null primary key,                    -- id = auth_id * 100 + 1:99
    auth_id int not null references naming_authority(auth_id),
    name varchar(255) not null,
    unique (auth_id, name)
);


create table id_tracker (
    -- Tracks the next available id to be assigned for each developer and
    -- table in the database.

    dev_id int not null references developer(id),
    table_id int not null,                          -- From enum 'db_table'.
    dev_id_multiplier int not null default 1000,
    next_id int not null default 1,
    primary key (dev_id, table_id)
);


create table enum (
    -- One-size-fits-all enum table...
    --
    -- To get the list of choices for enum 'foo':
    --     select enum_id, id, name from enum 
    --     where enum_id = (select id from enum
    --                      where enum_id = 101001 and name = 'foo')
    --     order by id
    --

    enum_id int not null,                           -- incorporates dev id
                                                    -- 101001 for enum of enums
    id int not null,                                -- incorporates dev id
    name varchar(255) not null,
    primary key (enum_id, id),
    unique (enum_id, name)
);

create table project (
    -- A project may be a library, program, or installation.  See Project page
    -- in google code project wiki.

    id int not null primary key,                    -- incorporates dev id
    auth_id int not null references naming_authority(auth_id),
    name varchar(255) not null,
    kind int not null,                              -- from enum 'project_kind'
    unique (auth_id, name)
);

create table uses (
    -- Tracks the "uses" clause, where one project "uses" another one.

    project_id_using int not null references project(id),
    project_id_used int not null references project(id),
    primary key (project_id_using, project_id_used)
);

-----------------------------------------------------------------------------
-----------------------------------------------------------------------------
-----------------------------------------------------------------------------
--
-- Everything above is just classification boilerplate.
--
-- Below is the nitty gritty...
--
-----------------------------------------------------------------------------
-----------------------------------------------------------------------------
-----------------------------------------------------------------------------


create table word (
    -- This is where the action is!  See Word page in google code project wiki.

    id int not null primary key,                    -- incorporates dev id
    project_id int not null references project(id),
    writable bool not null,
    name varchar(255) not null,
    kind int not null,                              -- from enum 'word_kind'
    unique (project_id, name)
);


create table question (
    -- Questions go here.

    id int not null primary key,                    -- incorporates dev id
    parent_kind int not null,                       -- From enum 'db_table'.
    parent_id int not null,                         -- May reference project
                                                    -- or word.
    kind int not null,                              -- From enum
                                                    -- 'question_kind'.
    enum_id int,                                    -- For kind = 'enum'
    question varchar(2000) not null
);


create table answer (
    -- Answers go here.

    id int not null primary key,                    -- incorporates dev id
    question_id int not null references question(id),

    -- what the answer is associated with:
    parent_kind int not null,                       -- From enum 'db_table'.
    parent_id int not null,                         -- May reference project
                                                    -- or word.

    int_answer int,
    str_answer varchar(2000)
);


create table node (
    -- The Abstract Syntax Tree (AST).  See AbstractSyntaxTree page in google
    -- code project wiki.  This table is not saved under source code control.

    id int not null primary key,                    -- Does NOT incorporate
                                                    -- dev id.
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

