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
    %for suffix, i, answer in (('@{}'.format(t_i), t_i, t_answer) for t_i, t_answer in enumerate(a)):
      <tr>
        <td><input class="up-input" name="${prefix|h}${q.name|h}${suffix|h}-up" type="checkbox"></td>
        <td><input class="del-input" name="${prefix|h}${q.name|h}${suffix|h}-del" type="checkbox"></td>
        %if hasattr(q_layout, 'single'):
          ${q_layout.single(q, answer, layouts, prefix, suffix)}
        %endif
        %if hasattr(q_layout, 'multi'):
          %for j, info in enumerate(q_layout.gen_multi_info(q, answer, layouts, prefix, suffix)):
            %if j > 0:
              <tr>
                <td class="up-no"></td>
                <td class="del-no"></td>
            %endif
              ${q_layout.multi(q, a, info, layouts, prefix, suffix)}
            </tr>
          %endfor
        %endif
      </tr>
    %endfor
    <tr>
      <td><input class="add-answer" name="${prefix|h}${q.name|h}-add" type="checkbox"></td>
      <td colspan="0">Add ${q.label|h}</td>
    </tr>
  </table>
  </td>
</tr>

