<%namespace name="atomic" file="atomic.tpl" />
<%namespace name="simple_series" file="simple_series.tpl" />
<%namespace name="series" file="series.tpl" />
<%namespace name="simple_choice" file="simple_choice.tpl" />
<%namespace name="choice" file="choice.tpl" />

<%
  layouts = {
    'atomic': atomic,
    'simple_series': simple_series,
    'series': series,
    'simple_choice': simple_choice,
    'choice': choice,
  }
%>

<form method="POST" action="/update_answers/${packages_name|u}/${package_name|u}/${word|u}">
  <%include file="question_list.tpl" args="qa_list=word_word.gen_questions(), layouts=layouts" />
  <input type="submit" value="submit" id="submit-question">
</form>
