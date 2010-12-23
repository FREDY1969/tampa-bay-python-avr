<!-- packages_name, package_name, word, word_word, q, a -->

<tr>
  <td class="label">{{q.label}}</td>
  <td class="omit-no"></td>
  <td class="answer-no"></td>
</tr>

<tr>
  <td colspan=3>
    <table class="repeat-table">
      %if a:
        <tr>
          <th class="repeat-title">up</th>
          <th class="repeat-title">del</th>
          <th class="empty-title"></th>
        </tr>
      %end
      %for i, answer in enumerate(a):
        <tr>
          <td class="up-td"><input name="{{q.label}}-up-{{i}}" type="checkbox"></td>
          <td class="del-td"><input name="{{q.label}}-del-{{i}}" type="checkbox"></td>
          <td class="answer"><input name="{{q.label}}-{{i}}" type="text"
          value="{{answer.value}}"></td>
        </tr>
      %end
      <tr>
        <td class="add-td"><input name="{{q.label}}-add" type="checkbox"></td>
        <td class="add-label" colspan=2>Add {{q.label}}</td>
      </tr>
    </table>
  </td>
</tr>
