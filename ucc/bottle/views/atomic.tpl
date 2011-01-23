<%!
    def has_rows(q, a):
        return False
%>

<%def name="single_line(q, a, layouts, prefix, suffix='')">
  <% print("atomic.tpl got q:", q, "a:", a) %>
  <td>
    <input class="atomic-input" name="${prefix|h}${q.name|h}${suffix|h}-answer" type="text" value="${a and a.value|h}">
  </td>
</%def>
