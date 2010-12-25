<%def name="single(q, a, layouts, prefix, suffix='')">
  <td>
    <select class="simple-choice-select" name="${prefix|h}${q.name|h}${suffix|h}-answer" size="1">
      %for name, value, _ in q.options:
        <option value="${value|h}">${name|h}</option>
      %endfor
    </select>
  </td>
</%def>
