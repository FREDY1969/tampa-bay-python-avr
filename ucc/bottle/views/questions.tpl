<form method="POST" action="/update_answers/{{packages_name}}/{{package_name}}/{{word}}">
  <table class="question-table">
    <tr>
      <th>Question</th>
      <th>Omit</th>
      <th>Answer</th>
    </tr>
    %for q_type, label, min_answers, max_answers, q_info in questions:
      %if min_answers == 0 and max_answers == 1:
        %include optional_question packages_name=packages_name, package_name=package_name, word=word, q_type=q_type, label=label, q_info=q_info
      %elif max_answers != 1:
        %include repeatable_question packages_name=packages_name, package_name=package_name, word=word, q_type=q_type, label=label, min_answers=min_answers, max_answers=max_answers, q_info=q_info
      %else:
        %include required_question packages_name=packages_name, package_name=package_name, word=word, q_type=q_type, label=label, q_info=q_info
      %end
    %end
  </table>
  <input type="submit" value="submit" id="submit-question">
</form>
