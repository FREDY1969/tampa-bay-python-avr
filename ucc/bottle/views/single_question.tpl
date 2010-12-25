<%page args="q, a, layouts, prefix" />

<% q_layout = layouts[q.layout()] %>

<tr>
  <td class="label">${q.label|h}</td>
  %if q.is_optional():
    <td class="omit-yes">
      <input name="${prefix|h}${q.name|h}-omit" type="checkbox">
    </td>
  %else:
    <td class="omit-no"></td>
  %endif
  %if hasattr(q_layout, 'single'):
    ${q_layout.single(q, a, layouts, prefix)}
  %else:
    <td class="answer-no"></td>
  %endif
</tr>

%if hasattr(q_layout, 'header') or hasattr(q_layout, 'multi'):
  <tr class="nested_row">
    <table class="nested_table">
      %if hasattr(q_layout, 'header'):
        <tr>
          ${q_layout.header(q)}
        </tr>
      %endif
      %if hasattr(q_layout.single):
        <tr>
          ${q_layout.single(q, a, layouts, prefix)}
        </tr>
      %endif
      %if hasattr(q_layout.multi):
        %for info in q_layout.gen_multi_info(q, a, layouts, prefix):
          <tr>
            ${q_layout.multi(q, a, info, layouts, prefix)}
          </tr>
        %endfor
      %endif
    </table>
  </tr>
%endif

