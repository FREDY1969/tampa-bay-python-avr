<%doc>

Each of the modules below has the following possible methods.  Both
single_line and rows may be defined:

    header(q)
        generates a series of <th> elements for column headers (if needed).
        This is optional and only used in conjunction with single_line.

    single_line(q, a, layouts, prefix, [suffix])
        generates a series of <td> elements (no labels).

    rows(q, a, layouts, prefix, [suffix])
        generates multiple <tr> elements (for "boxed" questions).  The caller
        is responsible for setting up the containing <table> element.

</%doc>

<%namespace name="atomic" file="atomic.tpl" />
<%namespace name="simple_series" file="simple_series.tpl" />
<%namespace name="series" file="series.tpl" />
<%namespace name="simple_choice" file="simple_choice.tpl" />
<%namespace name="choice" file="choice.tpl" />
<%namespace name="multichoice" file="multichoice.tpl" />

<%
  layouts = {
    'atomic': atomic,
    'simple_series': simple_series,
    'series': series,
    'simple_choice': simple_choice,
    'choice': choice,
    'multichoice': multichoice,
  }
%>

<form method="POST" action="/update_answers/${packages_name|u}/${package_name|u}/${word|u}">
  <table class="question-table">
    <tr class="question-header">
      <th>Question</th>
      <th>Omit</th>
      <th>Answer</th>
    </tr>
    <%include file="question_list.tpl" args="qa_list=word_word.gen_questions(), layouts=layouts" />
  </table>
  <input type="submit" value="submit" id="submit-question">
</form>
