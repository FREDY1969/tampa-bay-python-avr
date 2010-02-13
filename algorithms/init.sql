-- init.sql

insert into class_alias (reg_class, reg)
  select distinct reg_in_class.reg_class, alias.r2
    from reg_in_class inner join alias on reg_in_class.reg = alias.r1;

insert into worst (N, C, value)
  select N.id, C.id,
         (select ifnull(max(cnt),0)
            from (select CC.reg, count(alias.r2) as cnt
                    from reg_in_class CC inner join alias
                         on CC.reg = alias.r1
                   where CC.reg_class = C.id
                     and alias.r2 in (select NC.reg
                                        from reg_in_class NC
                                       where NC.reg_class = N.id)
                   group by CC.reg))
    from reg_class N cross join reg_class C;

-- reg_classes directly in each vertex:
insert into v_classes (v, C)
    select v, id
      from reg_class;

-- reg_classes in child vertexes (1 level):
insert or ignore into v_classes (v, C)
    select v.parent, vc.C
      from v_classes vc inner join vertex v on vc.v = v.id
     where v.parent is not null;

-- 2 levels:
insert or ignore into v_classes (v, C)
    select v.parent, vc.C
      from v_classes vc inner join vertex v1 on vc.v = v1.id
             inner join vertex v on v1.parent = v.id
     where v.parent is not null;

-- 4 levels:
insert or ignore into v_classes (v, C)
    select v.parent, vc.C
      from v_classes vc inner join vertex v1 on vc.v = v1.id
             inner join vertex v2 on v1.parent = v2.id
             inner join vertex v3 on v2.parent = v3.id
             inner join vertex v on v3.parent = v.id
     where v.parent is not null;

-- 4 levels:
insert or ignore into v_classes (v, C)
    select v.parent, vc.C
      from v_classes vc inner join vertex v1 on vc.v = v1.id
             inner join vertex v2 on v1.parent = v2.id
             inner join vertex v3 on v2.parent = v3.id
             inner join vertex v on v3.parent = v.id
     where v.parent is not null;

insert into bound (N, v, value)
    select n.id, v.id, count(distinct a.r2)
      from reg_class n cross join vertex v
             inner join reg_in_class nc on nc.reg_class = n.id
             inner join v_classes vc on v.id = vc.v
             inner join reg_in_class cc on cc.reg_class = vc.C
             left  join alias a on cc.reg = a.r1 and nc.reg = a.r2
     group by n.id, v.id;

analyze;
