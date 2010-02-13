-- avr.sql

insert into register (name) values ('r0');
insert into register (name) values ('r1');
insert into register (name) values ('r2');
insert into register (name) values ('r3');
insert into register (name) values ('r4');
insert into register (name) values ('r5');
insert into register (name) values ('r6');
insert into register (name) values ('r7');
insert into register (name) values ('r8');
insert into register (name) values ('r9');
insert into register (name) values ('r10');
insert into register (name) values ('r11');
insert into register (name) values ('r12');
insert into register (name) values ('r13');
insert into register (name) values ('r14');
insert into register (name) values ('r15');
insert into register (name) values ('r16');
insert into register (name) values ('r17');
insert into register (name) values ('r18');
insert into register (name) values ('r19');
insert into register (name) values ('r20');
insert into register (name) values ('r21');
insert into register (name) values ('r22');
insert into register (name) values ('r23');
insert into register (name) values ('r24');
insert into register (name) values ('r25');
insert into register (name) values ('r26');
insert into register (name) values ('r27');
insert into register (name) values ('r28');
insert into register (name) values ('r29');
insert into register (name) values ('r30');
insert into register (name) values ('r31');

insert into register (name) values ('d0');
insert into register (name) values ('d2');
insert into register (name) values ('d4');
insert into register (name) values ('d6');
insert into register (name) values ('d8');
insert into register (name) values ('d10');
insert into register (name) values ('d12');
insert into register (name) values ('d14');
insert into register (name) values ('d16');
insert into register (name) values ('d18');
insert into register (name) values ('d20');
insert into register (name) values ('d22');
insert into register (name) values ('d24');
insert into register (name) values ('d26');
insert into register (name) values ('d28');
insert into register (name) values ('d30');

insert into register (name) values ('X');
insert into register (name) values ('Y');
insert into register (name) values ('Z');

insert into alias (r1, r2) values ('r0', 'd0');
insert into alias (r1, r2) values ('r1', 'd0');
insert into alias (r1, r2) values ('r2', 'd2');
insert into alias (r1, r2) values ('r3', 'd2');
insert into alias (r1, r2) values ('r4', 'd4');
insert into alias (r1, r2) values ('r5', 'd4');
insert into alias (r1, r2) values ('r6', 'd6');
insert into alias (r1, r2) values ('r7', 'd6');
insert into alias (r1, r2) values ('r8', 'd8');
insert into alias (r1, r2) values ('r9', 'd8');
insert into alias (r1, r2) values ('r10', 'd10');
insert into alias (r1, r2) values ('r11', 'd10');
insert into alias (r1, r2) values ('r12', 'd12');
insert into alias (r1, r2) values ('r13', 'd12');
insert into alias (r1, r2) values ('r14', 'd14');
insert into alias (r1, r2) values ('r15', 'd14');
insert into alias (r1, r2) values ('r16', 'd16');
insert into alias (r1, r2) values ('r17', 'd16');
insert into alias (r1, r2) values ('r18', 'd18');
insert into alias (r1, r2) values ('r19', 'd18');
insert into alias (r1, r2) values ('r20', 'd20');
insert into alias (r1, r2) values ('r21', 'd20');
insert into alias (r1, r2) values ('r22', 'd22');
insert into alias (r1, r2) values ('r23', 'd22');
insert into alias (r1, r2) values ('r24', 'd24');
insert into alias (r1, r2) values ('r25', 'd24');
insert into alias (r1, r2) values ('r26', 'd26');
insert into alias (r1, r2) values ('r27', 'd26');
insert into alias (r1, r2) values ('r28', 'd28');
insert into alias (r1, r2) values ('r29', 'd28');
insert into alias (r1, r2) values ('r30', 'd30');
insert into alias (r1, r2) values ('r31', 'd30');

insert into alias (r1, r2) values ('r26', 'X');
insert into alias (r1, r2) values ('r27', 'X');
insert into alias (r1, r2) values ('r28', 'Y');
insert into alias (r1, r2) values ('r29', 'Y');
insert into alias (r1, r2) values ('r30', 'Z');
insert into alias (r1, r2) values ('r31', 'Z');

insert into alias (r1, r2) values ('d26', 'X');
insert into alias (r1, r2) values ('d28', 'Y');
insert into alias (r1, r2) values ('d30', 'Z');

insert into alias (r1, r2) select r2, r1 from alias;
insert into alias (r1, r2) select name, name from register;

insert into vertex (id) values (1);                     -- 1, 2
  insert into vertex (id, parent) values (2, 1);        -- 3
    insert into vertex (id, parent) values (3, 2);      -- 4
      insert into vertex (id, parent) values (4, 3);    -- 5
        insert into vertex (id, parent) values (5, 4);  -- 6
    insert into vertex (id, parent) values (6, 2);      -- 7
  insert into vertex (id, parent) values (7, 1);        -- 8

insert into reg_class (id, name, v) values (1, 'single', 1);
insert into reg_in_class (reg_class, reg)
  select 1, name from register where name like 'r%';

insert into reg_class (id, name, v) values (2, 'pair', 1);
insert into reg_in_class (reg_class, reg)
  select 2, name from register where name like 'd%';

insert into reg_class (id, name, v) values (3, 'immed', 2);
insert into reg_in_class (reg_class, reg)
  select 3, name from register where name like 'r__' and name >= 'r16';

insert into reg_class (id, name, v) values (4, 'immed_word', 3);
insert into reg_in_class (reg_class, reg) values (4, 'd24');
insert into reg_in_class (reg_class, reg) values (4, 'd26');
insert into reg_in_class (reg_class, reg) values (4, 'd28');
insert into reg_in_class (reg_class, reg) values (4, 'd30');

insert into reg_class (id, name, v) values (5, 'index', 4);
insert into reg_in_class (reg_class, reg) values (5, 'X');
insert into reg_in_class (reg_class, reg) values (5, 'Y');
insert into reg_in_class (reg_class, reg) values (5, 'Z');

insert into reg_class (id, name, v) values (6, 'offset', 5);
insert into reg_in_class (reg_class, reg) values (6, 'Y');
insert into reg_in_class (reg_class, reg) values (6, 'Z');

insert into reg_class (id, name, v) values (7, 'fmul', 6);
insert into reg_in_class (reg_class, reg) values (7, 'r16');
insert into reg_in_class (reg_class, reg) values (7, 'r17');
insert into reg_in_class (reg_class, reg) values (7, 'r18');
insert into reg_in_class (reg_class, reg) values (7, 'r19');
insert into reg_in_class (reg_class, reg) values (7, 'r20');
insert into reg_in_class (reg_class, reg) values (7, 'r21');
insert into reg_in_class (reg_class, reg) values (7, 'r22');
insert into reg_in_class (reg_class, reg) values (7, 'r23');

insert into reg_class (id, name, v) values (8, 'mul_out', 7);
insert into reg_in_class (reg_class, reg) values (8, 'd0');

