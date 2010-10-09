.mode column

.headers OFF
.width 50
select 'there should be no results from the next query';

.headers ON
.width 6 3 3
select rul.id as rul_id, ru1.id as id1, ru1.id as id2
  from reg_use_linkage rul
       inner join reg_use ru1
         on rul.reg_use_1 = ru1.id
       inner join reg_use ru2
         on rul.reg_use_2 = ru2.id
 where not broken
   and (   ru1.block_id != ru2.block_id
        or ru1.reg_group_id != ru2.reg_group_id);

.headers OFF
.width 50
select 'this is the linkage info';

.headers ON
.width 6 6 10 3 6 3 6
select rul.id as rul_id, ru1.block_id as blk_id, ru1.reg_group_id as reg_grp_id,
       ru1.id as id1, ru1.abs_order_in_block as order1,
       ru2.id as id2, ru2.abs_order_in_block as order2
  from reg_use_linkage rul
       inner join reg_use ru1
         on rul.reg_use_1 = ru1.id
       inner join reg_use ru2
         on rul.reg_use_2 = ru2.id
 where not broken
   and ru1.block_id notnull
   and ru1.abs_order_in_block notnull
   and ru2.block_id notnull
   and ru2.abs_order_in_block notnull
 order by ru1.block_id, order1, ru1.reg_group_id;
