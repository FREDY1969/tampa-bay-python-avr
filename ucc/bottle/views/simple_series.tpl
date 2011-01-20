<%def name="header(q)">
  %for sub_q in q.subquestions:
    <th>${sub_q.label|h}</th>
  %endfor
</%def>

<%def name="single_line(q, a, layouts, prefix, suffix='')">
  <% print("simple_series.tpl got q:", q, "a:", a) %>
  <% sub_prefix = "{}{}{}.".format(prefix, q.name, suffix) %>
  %for sub_q, sub_a in q.gen_subquestions(a):
    ${layouts[sub_q.layout()].single_line(sub_q, sub_a, layouts, sub_prefix)}
  %endfor
</%def>
