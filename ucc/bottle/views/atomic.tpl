<%def name="single_line(q, a, layouts, prefix, suffix='')">
  <td>
    <input class="atomic-input" name="${prefix|h}${q.name|h}${suffix|h}-answer" type="text" value="${a.value|h}">
  </td>
</%def>
