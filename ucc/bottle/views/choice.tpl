<%!
    import itertools
%>

<%def name="rows(q, a, layouts, prefix, suffix='')">
  %for name, value, subquestions in q.options:
    <tr>
      <td class="choice-checkbox">
        %if a.tag == value:
          <input class="choice-checkbox" name="${prefix|h}${q.name|h}${suffix|h}-answer" type="checkbox" checked value="${value|h}">
        %else:
          <input class="choice-checkbox" name="${prefix|h}${q.name|h}${suffix|h}-answer" type="checkbox" value="${value|h}">
        %endif
      </td>
      <td class="choice-label">${name|h}</td>
    </tr>
    %if subquestions:
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
