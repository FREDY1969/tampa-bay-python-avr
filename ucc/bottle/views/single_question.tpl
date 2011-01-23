<%page args="q, a, layouts, prefix" />

<% print("single_question.tpl got q:", q, "a:", a) %>

<% q_layout = layouts[q.layout()] %>

<tr>
  <td class="label">${q.label|h}</td>
  %if q.is_optional():
    %if a and a.is_answered():
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

%if hasattr(q_layout, 'header') or q_layout.attr.has_rows(q, a):
  <tr class="nested-table">
    <td class="nested-table" colspan="0">
      <table class="nested-table">
        %if hasattr(q_layout, 'header'):
          <tr>
            ${q_layout.header(q)}
          </tr>
          %if hasattr(q_layout, 'single_line'):
            <tr>
              ${q_layout.single_line(q, a, layouts, prefix)}
            </tr>
          %endif
        %endif
        %if q_layout.attr.has_rows(q, a):
          ${q_layout.rows(q, a, layouts, prefix)}
        %endif
      </table>
    </td>
  </tr>
%endif

