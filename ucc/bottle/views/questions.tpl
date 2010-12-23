<form method="POST" action="/update_answers/{{packages_name}}/{{package_name}}/{{word}}">
  <table class="question-table">
    <tr>
      <th>Question</th>
      <th>Omit</th>
      <th>Answer</th>
    </tr>
    %for q, a in word_word.gen_questions():
      %if q.is_optional():
        %include optional_question packages_name=packages_name, package_name=package_name, word=word, word_word=word_word, q=q, a=a
      %elif q.is_repeatable():
        %include repeatable_question packages_name=packages_name, package_name=package_name, word=word, word_word=word_word, q=q, a=a
      %else:
        %include required_question packages_name=packages_name, package_name=package_name, word=word, word_word=word_word, q=q, a=a
      %end
    %end
  </table>
  <input type="submit" value="submit" id="submit-question">
</form>
