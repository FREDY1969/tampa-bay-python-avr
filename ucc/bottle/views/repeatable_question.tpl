<%page args="q, a, layouts, prefix" />

<% q_layout = layouts[q.layout()] %>

<tr>
  <td class="label">${q.label|h}</td>
  <td class="omit-no"></td>
  <td class="answer-no"></td>
</tr>

<tr>
  <td colspan="0">
    <table class="nested_table">
      <tr>
        <th>up</th>
        <th>del</th>
        %if hasattr(q_layout, 'header'):
          ${q_layout.header(q)}
        %else:
          <th colspan="0"></th>
        %endif
      </tr>
      %for suffix, i, answer in (('@{}'.format(t_i), t_i, t_answer) for t_i, t_answer in enumerate(a or ())):
        <tr>
          <td><input class="up-input" name="${prefix|h}${q.name|h}${suffix|h}-up" type="checkbox"></td>
          <td><input class="del-input" name="${prefix|h}${q.name|h}${suffix|h}-del" type="checkbox"></td>
          %if hasattr(q_layout, 'single_line'):
            ${q_layout.single_line(q, answer, layouts, prefix, suffix)}
          %else:
            <td>
              <table class="boxed-question">
                ${q_layout.rows(q, answer, layouts, prefix, suffix)}
              </table>
            </td>
          %endif
        </tr>
      %endfor
      %if q.max is None or len(a or ()) < q.max:
        <tr>
          <td><input class="add-answer" name="${prefix|h}${q.name|h}-add" type="checkbox"></td>
          <td colspan="0">Add ${q.label|h}</td>
        </tr>
      %endif
    </table>
  </td>
</tr>

