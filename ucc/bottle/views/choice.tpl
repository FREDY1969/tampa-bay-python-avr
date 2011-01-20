<%!
    from ucc.word import questions
    import itertools
%>

<%def name="rows(q, a, layouts, prefix, suffix='')">
  %for name, value, subquestions in q.options:
    <tr>
      <td class="choice-input">
        <% checked = 'checked' if a and a.option_present(value) else '' %>
        <input class="choice-input" name="${prefix|h}${q.name|h}${suffix|h}-answer" type="${q.input_type}" ${checked} value="${value|h}">
      </td>
      <td class="choice-label">${name|h}</td>
    </tr>
    %if a and a.option_present(value) and subquestions:
      <tr class="choice-subquestions">
        <td></td>
        <td class="choice-subquestions">
          <table class="choice-subquestions">
            <%include file="question_list.tpl" args="qa_list=q.gen_subquestions((name, value, subquestions), a), layouts=layouts, prefix='{}{}{}.'.format(prefix, q.name, suffix)" />
          </table>
        </td>
      </tr>
    %endif
  %endfor
</%def>
