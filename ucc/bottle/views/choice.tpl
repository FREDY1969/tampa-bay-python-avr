<%!
    import itertools
%>

<%
    def gen_multi_info(q, a, layouts, prefix, suffix=''):
        return q.options
%>

<%def name="multi(q, answer, opt, layouts, prefix, suffix='')">
  <td>
    <input class="choice-checkbox" name="${prefix|h}${q.name|h}${suffix|h}-answer" type="checkbox" value="${opt[1]|h}">
  </td>
  %if opt[2]:
    <td class="choice-label">
      <table class="choice-option">
        <tr>
          <td class="simple-choice-label">${opt[0]|h}</td>
        </tr>
        <tr>
          <td>
            %if answer.tag == opt[1]:
              <%include file="question_list.tpl" args="qa_list=zip(q.options[2], a.subanswers), layouts=layouts, prefix='{}{}{}.'.format(prefix, q.name, suffix)" />
            %else:
              <%include file="question_list.tpl" args="qa_list=zip(q.options[2], itertools.repeat(None)), layouts=layouts, prefix='{}{}{}.'.format(prefix, q.name, suffix)" />
            %endif
          </td>
        </tr>
      </table>
    </td>
  %else:
    <td class="simple-choice-label">${opt[0]|h}</td>
  %endif
</%def>
