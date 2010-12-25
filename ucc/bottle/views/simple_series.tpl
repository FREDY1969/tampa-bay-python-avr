<%def name="header(q)">
  %for sub_q in q.subquestions:
    <th>${sub_q.label|h}</th>
  %endfor
</%def>

<%def name="single(q, a, layouts, prefix, suffix='')">
  <% sub_prefix = "{}{}{}.".format(prefix, q.name, suffix) %>
  %for sub_q in q.subquestions:
    ${layouts[sub_q.layout()].single(sub_q, getattr(a, sub_q.name), layouts, sub_prefix)}
  %endfor
</%def>
