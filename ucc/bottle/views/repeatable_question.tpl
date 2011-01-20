<%page args="q, a, layouts, prefix" />

<% print("repeatable_question.tpl got q:", q, "a:", a) %>

<% q_layout = layouts[q.layout()] %>

<tr>
  <td class="label">${q.label|h}</td>
  <td class="omit-no"></td>
  <td class="answer-no"></td>
</tr>

<tr>
  <td colspan="0">
    <table class="nested-table">
      <tr>
        %if q.is_orderable():
          <th></th>
        %endif
        <th></th>
        %if hasattr(q_layout, 'header'):
          ${q_layout.header(q)}
        %else:
          <th colspan="0"></th>
        %endif
      </tr>
      %for suffix, i, answer in (('@{}'.format(t_i), t_i, t_answer) for t_i, t_answer in enumerate(a or ())):
        <tr>
          %if q.is_orderable():
            <td class="up-input">
            %if i != 0:
              <a class="up-input" href="/up/${packages_name|h}/${package_name|h}/${word|h}/${i}/${prefix|h}${q.name|h}">up</a>
            %endif
            </td>
          %endif
          <td class="del-input">
            <a class="del-input" href="/del/${packages_name|h}/${package_name|h}/${word|h}/${i}/${prefix|h}${q.name|h}">del</a>
          </td>
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
          <td colspan="0">
            <a class="add-answer" href="/append/${packages_name|h}/${package_name|h}/${word|h}/${prefix|h}${q.name|h}">Add ${q.label|h}</a>
          </td>
        </tr>
      %endif
    </table>
  </td>
</tr>

