<form method="POST" action="/update_answers/{{packages_name}}/{{package_name}}/{{word}}">
  <table class="question-table">
    <tr>
      <th>Add</th>
      <th>Question</th>
      <th>Omit</th>
      <th>Answer</th>
    </tr>
    %for q_type, label, min_answers, max_answers, q_info in questions:
      <tr>
        %if min_answers == 0 and max_answers == 1:
          %include optional_question packages_name=packages_name, package_name=package_name, word=word, q_type=q_type, label=label q_info=q_info
        %elif max_answers != 1:
          %include repeatable_question packages_name=packages_name, package_name=package_name, word=word, q_type=q_type, min_answers=min_answers, max_answers=max_answers q_info=q_info
        %else:
          %include required_question packages_name=packages_name, package_name=package_name, word=word, q_type=q_type, label=label q_info=q_info
        %end
      </tr>
    %end

      <td class="add-yes">
        <input type="checkbox">
      </td>

      <td class="label">
        argument
      </td>

      <td class="omit-no"></td>
      <td class="answer-no"></td>
    </tr>

    <tr>
      <td></td>
      <td class="del-yes" colspan="3">
        <table class="repeat-table">
          <tr>
            <td class="up-yes"><input type="checkbox"></td>
            <td class="del-yes"><input type="checkbox"></td>
            <td class="repeat-answer">
              <input type="text">
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
  <input type="submit" value="submit" id="submit-question">
</form>
