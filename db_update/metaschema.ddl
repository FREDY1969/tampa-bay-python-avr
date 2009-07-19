-- metaschema.ddl

create table db_table (
    id integer not null,
    version int not null,
    table_name varchar(255) not null,
    table_order int not null,
    python_update varchar(4000),        -- python statements (source code)
                                        -- using 'db_cur' to update table
                                        -- run after data imported (if any).
    primary key (id, version),
    unique (table_name, version)
);

create table db_column (
    id integer not null,
    version int not null,
    table_id integer not null,
    position int not null,
    col_name varchar(255),              -- blank for table level declarations
    definition varchar(1000),
    python_default varchar(4000),       -- python statements (source code)
                                        -- using 'row' dict and setting
                                        -- 'default'.

    primary key (id, version),
    foreign key (table_id, version) references db_table (id, version)
    unique (table_id, col_name, version)
);
