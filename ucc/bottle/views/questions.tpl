<form method="POST" action="/update_answers/${packages_name|u}/${package_name|u}/${word|u}">
  <table class="question-table">
    <tr>
      <th>Question</th>
      <th>Omit</th>
      <th>Answer</th>
    </tr>
    %for q, a in word_word.gen_questions():
      %if q.is_repeatable():
        ##<%include file="repeatable_question.tpl" />
        <tr><td>repeating questions not ready yet</td></tr>
      %else:
        ##<%include file="single_question.tpl" />
        <tr><td>single questions not ready yet</td></tr>
      %endif
    %endfor
  </table>
  <input type="submit" value="submit" id="submit-question">
</form>
