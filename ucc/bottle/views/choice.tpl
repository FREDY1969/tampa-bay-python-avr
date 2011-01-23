<%!
    from ucc.word import questions
    import itertools

    def has_rows(q, a):
        if not a: return False
        for name, value, subquestions in q.options:
            if a.option_present(value):
                return bool(subquestions)
        return False
%>

<%def name="single_line(q, a, layouts, prefix, suffix='')">
  <td>
    <select class="simple-choice-select" name="${prefix|h}${q.name|h}${suffix|h}-answer" size="1">
      %for name, value, _ in q.options:
        %if a and a.option_present(value):
          <option value="${value|h}" selected>${name|h}</option>
        %else:
          <option value="${value|h}">${name|h}</option>
        %endif
      %endfor
    </select>
  </td>
</%def>

<%def name="rows(q, a, layouts, prefix, suffix='')">
  %for name, value, subquestions in q.options:
    %if a.option_present(value):
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
