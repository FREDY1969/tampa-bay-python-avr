<%
    def gen_multi_info(q, a, layouts, prefix, suffix=''):
        return q.subquestions
%>

<%def name="multi(q, answer, sub_q, layouts, prefix, suffix='')">
  <% sub_prefix = "{}{}{}.".format(prefix, q.name, suffix) %>
  <td>${sub_q.label|h}</td>

  ##FIX: This should box complicated sub questions!
  ${layouts[sub_q.layout()].single(sub_q, a, layouts, sub_prefix)}

</%def>
