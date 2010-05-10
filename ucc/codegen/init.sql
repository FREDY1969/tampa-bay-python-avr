-- init.sql

insert into alias (r1, r2) select name, name from register;

insert into class_alias (reg_class, reg)
  select distinct reg_in_class.reg_class, alias.r2
    from reg_in_class inner join alias on reg_in_class.reg = alias.r1;

-- start out by inserting a vertex for each reg_class:
insert into vertex (id)
  select id from reg_class;

-- and update the reg_classes to point to the vertexes:
update reg_class set v = id;

-- Then update all reg_classes with the same class_aliases to point to the
-- lowest number vertex.  This will share vertexes by equivalent reg_classes.
update reg_class set v = (
     select r2.id
       from reg_class r2
      where not exists (  select reg
                            from class_alias a1
                           where a1.reg_class = reg_class.id
                        except
                          select reg
                            from class_alias a2
                           where a2.reg_class = r2.id)
        and not exists (  select reg
                            from class_alias a3
                           where a3.reg_class = r2.id
                        except
                          select reg
                            from class_alias a4
                           where a4.reg_class = reg_class.id)
      order by id
      limit 1);

-- delete unused vertexes:
delete from vertex
 where not exists (select null from reg_class where v = vertex.id);

-- Then update all reg_classes with the same class_aliases to point to the
-- lowest number vertex.  This will share vertexes by equivalent reg_classes.
update vertex set parent = (
     select p.id
       from vertex p cross join class_alias ap on p.id = ap.reg_class
      where p.id != vertex.id
        and -- vertex is subset of p
            not exists (  select reg
                            from class_alias a1
                            where a1.reg_class = vertex.id
                        except
                          select reg
                            from class_alias ap2
                            where ap2.reg_class = p.id)
      group by p.id
      order by count(ap.reg)
      limit 1);

-- set bit_mask field in vertexes:
update vertex set bit_mask = 1 << (id - 1);

update vertex set vertex_set = (
    select sum(v.bit_mask)
      from vertex v
     where -- vertex v is subset of vertex
           not exists (  select reg
                           from class_alias a1
                           where a1.reg_class = v.id
                       except
                         select reg
                           from class_alias ap2
                           where ap2.reg_class = vertex.id));

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

insert into reg_class_subsets (rc1, rc2, subset)
    select rc.id, vc.C, vc.C
      from v_classes vc
             inner join reg_class rc
               on rc.v = vc.v;

insert or ignore into reg_class_subsets (rc1, rc2, subset)
    select rc2, rc1, rc2
      from reg_class_subsets;

analyze;
