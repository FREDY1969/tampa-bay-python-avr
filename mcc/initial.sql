-- initial.sql

-- enums:

-- enum
insert into enum (id, enum_id, name) values (1, 1, 'enum');
insert into enum (id, enum_id, name) values (2, 1, 'node_kind');

-- node_kind
insert into enum (enum_id, name) values (2, 'literal');
insert into enum (enum_id, name) values (2, 'word');
insert into enum (enum_id, name) values (2, 'byte_code_block');
insert into enum (enum_id, name) values (2, 'byte_code');
insert into enum (enum_id, name) values (2, 'machine_code_block');
insert into enum (enum_id, name) values (2, 'machine_inst');

