<%page args="q, a, layouts, prefix" />

<% q_layout = layouts[q.layout()] %>

<tr>
  <td class="label">${q.label|h}</td>
  %if q.is_optional():
    %if a.is_answered():
      <td class="omit-yes">
        <input name="${prefix|h}${q.name|h}-omit" type="checkbox">
      </td>
    %else:
      <td class="omit-yes">
        <input name="${prefix|h}${q.name|h}-omit" type="checkbox" checked>
      </td>
    %endif
  %else:
    <td class="omit-no"></td>
  %endif
  %if hasattr(q_layout, 'single_line') and not hasattr(q_layout, 'header'):
    ${q_layout.single_line(q, a, layouts, prefix)}
  %else:
    <td class="answer-no"></td>
  %endif
</tr>

%if hasattr(q_layout, 'header') or hasattr(q_layout, 'rows'):
  <tr class="nested_row">
    <table class="nested_table">
      %if hasattr(q_layout, 'header'):
        <tr>
          ${q_layout.header(q)}
        </tr>
      %endif
      %if hasattr(q_layout.single_line):
        <tr>
          ${q_layout.single_line(q, a, layouts, prefix)}
        </tr>
      %else:
        ${q_layout.rows(q, a, layouts, prefix)}
      %endif
    </table>
  </tr>
%endif

