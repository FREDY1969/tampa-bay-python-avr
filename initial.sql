-- initial.sql

-- only one naming_authority so far...
insert into naming_authority (auth_id, name, email_url, email_name)
 values (1, 'Python-AVR', 'gmail.com', 'jasonkeene');


-- developers:
insert into developer (id, auth_id, name) values (101, 1, 'Bruce');
insert into developer (id, auth_id, name) values (102, 1, 'Bram');
insert into developer (id, auth_id, name) values (103, 1, 'Jason');
insert into developer (id, auth_id, name) values (104, 1, 'Michael');

-- enums:

-- enum
insert into enum (enum_id, id, name) values (101001, 101001, 'enum');
insert into enum (enum_id, id, name) values (101001, 101002, 'db_table');
insert into enum (enum_id, id, name) values (101001, 101003, 'project_kind');
insert into enum (enum_id, id, name) values (101001, 101004, 'word_kind');
insert into enum (enum_id, id, name) values (101001, 101005, 'question_kind');
insert into enum (enum_id, id, name) values (101001, 101006, 'node_kind');

-- db_table
insert into enum (enum_id, id, name) values (101002, 101020, 'naming_authority');
insert into enum (enum_id, id, name) values (101002, 101021, 'developer');
insert into enum (enum_id, id, name) values (101002, 101022, 'id_tracker');
insert into enum (enum_id, id, name) values (101002, 101023, 'enum');
insert into enum (enum_id, id, name) values (101002, 101024, 'project');
insert into enum (enum_id, id, name) values (101002, 101025, 'uses');
insert into enum (enum_id, id, name) values (101002, 101026, 'word');
insert into enum (enum_id, id, name) values (101002, 101027, 'question');
insert into enum (enum_id, id, name) values (101002, 101028, 'answer');
insert into enum (enum_id, id, name) values (101002, 101029, 'node');

-- project_kind
insert into enum (enum_id, id, name) values (101003, 101040, 'library');
insert into enum (enum_id, id, name) values (101003, 101041, 'program');
insert into enum (enum_id, id, name) values (101003, 101042, 'installation');

-- word_kind
insert into enum (enum_id, id, name) values (101004, 101050, 'compiler');
insert into enum (enum_id, id, name) values (101004, 101051, 'byte code');
insert into enum (enum_id, id, name) values (101004, 101052, 'machine code');

-- question_kind
insert into enum (enum_id, id, name) values (101005, 101080, 'yes_no');
insert into enum (enum_id, id, name) values (101005, 101081, 'int');
insert into enum (enum_id, id, name) values (101005, 101082, 'fractional');
insert into enum (enum_id, id, name) values (101005, 101083, 'string');

-- node_kind
insert into enum (enum_id, id, name) values (101006, 101090, 'literal');
insert into enum (enum_id, id, name) values (101006, 101091, 'word');
insert into enum (enum_id, id, name) values (101006, 101092, 'byte_code_block');
insert into enum (enum_id, id, name) values (101006, 101093, 'byte_code');
insert into enum (enum_id, id, name) values (101006, 101094, 'machine_code_block');
insert into enum (enum_id, id, name) values (101006, 101095, 'machine_inst');


-- id_tracker:
insert into id_tracker (dev_id, table_id, dev_id_multiplier, next_id)
values (101, 101023, 1000, 101110);
insert into id_tracker (dev_id, table_id, dev_id_multiplier, next_id)
values (101, 101024, 1000, 101002);


-- project:
insert into project (id, auth_id, name, kind)
values (101001, 1, '__builtin__', 101040);

