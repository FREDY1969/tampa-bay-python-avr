<%def name="single_line(q, a, layouts, prefix, suffix='')">
  <td>
    <select class="simple-choice-select" name="${prefix|h}${q.name|h}${suffix|h}-answer" size="1">
      %for name, value, _ in q.options:
        %if a.tag == value:
          <option value="${value|h}" selected>${name|h}</option>
        %else:
          <option value="${value|h}">${name|h}</option>
        %endif
      %endfor
    </select>
  </td>
</%def>
