<tr>
  <td class="label">${q.label|h}</td>
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
      %endif
      %for i, answer in enumerate(a):
        <tr>
          <td class="up-td"><input name="${q.name|h}-up-${i|h}" type="checkbox"></td>
          <td class="del-td"><input name="${q.name|h}-del-${i|h}" type="checkbox"></td>
          <td class="answer"><input name="${q.name|h}-${i|h}" type="text"
          value="${answer.value|h}"></td>
        </tr>
      %endfor
      <tr>
        <td class="add-td"><input name="${q.name|h}-add" type="checkbox"></td>
        <td class="add-label" colspan=2>Add ${q.label|h}</td>
      </tr>
    </table>
  </td>
</tr>
