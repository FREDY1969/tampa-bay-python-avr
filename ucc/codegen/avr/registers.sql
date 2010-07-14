-- registers.sql

-- Defines the registers, aliases and reg_classes for the Atmel AVR
-- architecture.

-- primary registers:
insert into register (name, is_primary) values ('r0', 1);
insert into register (name, is_primary) values ('r1', 1);
insert into register (name, is_primary) values ('r2', 1);
insert into register (name, is_primary) values ('r3', 1);
insert into register (name, is_primary) values ('r4', 1);
insert into register (name, is_primary) values ('r5', 1);
insert into register (name, is_primary) values ('r6', 1);
insert into register (name, is_primary) values ('r7', 1);
insert into register (name, is_primary) values ('r8', 1);
insert into register (name, is_primary) values ('r9', 1);
insert into register (name, is_primary) values ('r10', 1);
insert into register (name, is_primary) values ('r11', 1);
insert into register (name, is_primary) values ('r12', 1);
insert into register (name, is_primary) values ('r13', 1);
insert into register (name, is_primary) values ('r14', 1);
insert into register (name, is_primary) values ('r15', 1);
insert into register (name, is_primary) values ('r16', 1);
insert into register (name, is_primary) values ('r17', 1);
insert into register (name, is_primary) values ('r18', 1);
insert into register (name, is_primary) values ('r19', 1);
insert into register (name, is_primary) values ('r20', 1);
insert into register (name, is_primary) values ('r21', 1);
insert into register (name, is_primary) values ('r22', 1);
insert into register (name, is_primary) values ('r23', 1);
insert into register (name, is_primary) values ('r24', 1);
insert into register (name, is_primary) values ('r25', 1);
insert into register (name, is_primary) values ('r26', 1);
insert into register (name, is_primary) values ('r27', 1);
insert into register (name, is_primary) values ('r28', 1);
insert into register (name, is_primary) values ('r29', 1);
insert into register (name, is_primary) values ('r30', 1);
insert into register (name, is_primary) values ('r31', 1);

-- double registers:
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

-- indirect registers:
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

-- all of the above aliases are symetrical:
insert into alias (r1, r2) select r2, r1 from alias;

-- register classes:
insert into reg_class (id, name) values (1, 'single');
insert into reg_in_class (reg_class, reg)
  select 1, name from register where name like 'r%';

insert into reg_class (id, name, num_registers) values (2, 'pair', 2);
insert into reg_in_class (reg_class, reg)
  select 2, name from register where name like 'd%';

insert into reg_class (id, name) values (3, 'immed');
insert into reg_in_class (reg_class, reg)
  select 3, name from register where name like 'r__' and name >= 'r16';

insert into reg_class (id, name, num_registers) values (4, 'immed_pair', 2);
insert into reg_in_class (reg_class, reg)
  select 4, name from register where name like 'd__' and name >= 'd16';

insert into reg_class (id, name, num_registers) values (5, 'immed_word', 2);
insert into reg_in_class (reg_class, reg) values (5, 'd24');
insert into reg_in_class (reg_class, reg) values (5, 'd26');
insert into reg_in_class (reg_class, reg) values (5, 'd28');
insert into reg_in_class (reg_class, reg) values (5, 'd30');

insert into reg_class (id, name, num_registers) values (6, 'indirect', 2);
insert into reg_in_class (reg_class, reg) values (6, 'X');
insert into reg_in_class (reg_class, reg) values (6, 'Y');
insert into reg_in_class (reg_class, reg) values (6, 'Z');

insert into reg_class (id, name, num_registers) values (7, 'offset', 2);
insert into reg_in_class (reg_class, reg) values (7, 'Y');
insert into reg_in_class (reg_class, reg) values (7, 'Z');

insert into reg_class (id, name, num_registers) values (8, 'lpm', 2);
insert into reg_in_class (reg_class, reg) values (8, 'Z');

insert into reg_class (id, name) values (9, 'fmul');
insert into reg_in_class (reg_class, reg) values (9, 'r16');
insert into reg_in_class (reg_class, reg) values (9, 'r17');
insert into reg_in_class (reg_class, reg) values (9, 'r18');
insert into reg_in_class (reg_class, reg) values (9, 'r19');
insert into reg_in_class (reg_class, reg) values (9, 'r20');
insert into reg_in_class (reg_class, reg) values (9, 'r21');
insert into reg_in_class (reg_class, reg) values (9, 'r22');
insert into reg_in_class (reg_class, reg) values (9, 'r23');

insert into reg_class (id, name, num_registers) values (10, 'fmul_pair', 2);
insert into reg_in_class (reg_class, reg) values (10, 'd16');
insert into reg_in_class (reg_class, reg) values (10, 'd18');
insert into reg_in_class (reg_class, reg) values (10, 'd20');
insert into reg_in_class (reg_class, reg) values (10, 'd22');

insert into reg_class (id, name, num_registers) values (11, 'mul_out', 2);
insert into reg_in_class (reg_class, reg) values (11, 'd0');

