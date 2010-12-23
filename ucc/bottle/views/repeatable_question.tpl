<!-- packages_name=packages_name, package_name=package_name, word=word,
q_type=q_type, label=label,
min_answers=min_answers, max_answers=max_answers, q_info=q_info
-->

<tr>
  <td class="label">{{label}}</td>
  <td class="omit-no"></td>
  <td class="answer-no"></td>
</tr>

<tr>
  <td colspan=3>
    <table class="repeat-table">
      %if q_info:
        <tr>
          <th class="repeat-title">up</th>
          <th class="repeat-title">del</th>
          <th class="empty-title"></th>
        </tr>
      %end
      %for i, answer in enumerate(q_info):
        <tr>
          <td class="up-td"><input name="{{label}}-up-{{i}}" type="checkbox"></td>
          <td class="del-td"><input name="{{label}}-del-{{i}}" type="checkbox"></td>
          <td class="answer"><input name="{{label}}-{{i}}" type="text" value="{{answer}}"></td>
        </tr>
      %end
      <tr>
        <td class="add-td"><input name="{{label}}-add" type="checkbox"></td>
        <td class="add-label" colspan=2>Add {{label}}</td>
      </tr>
    </table>
  </td>
</tr>
