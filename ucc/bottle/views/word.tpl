%rebase base title=package_name, css_files=['word.css']

<div class="menu">
  <a class="menu_item" href="/">Close</a>
  %if word is None:
    <a class="menu_item" href="/compile/{{package_dir}}/{{package_name}}">Compile</a>
    <a class="menu_item" href="/load/{{package_dir}}/{{package_name}}">Load</a>
  %else:
    <a class="menu_item" href="/compile/{{package_dir}}/{{package_name}}/{{word}}">Compile</a>
    <a class="menu_item" href="/load/{{package_dir}}/{{package_name}}/{{word}}">Load</a>
  %end
</div>

<table id="outer-table">
<col id="index-col"><col id="word-col">
<tr>
  <td id="contents" rowspan=3>
    <ul class="outer-contents">
      %for decl_package_dir, decl_package_name, decl_word, local_words in index:
        <li class="outer-element">
          <a class="decl-link" href="/{{decl_package_dir}}/{{decl_package_name}}/{{decl_word}}">
            {{decl_word}}
          </a>
        </li>
        <ul class="inner-contents">
          %for local_word in local_words:
            <li class="inner-element">
              <a class="word-link" href="/{{package_dir}}/{{package_name}}/{{local_word}}">
                {{local_word}}
              </a>
            </li>
          %end
          <li class="create-word-li">
            <form method="POST" action="/create_word/{{package_dir}}/{{package_name}}">
              <input name="decl_package_dir" type="hidden" value="{{decl_package_dir}}"></input>
              <input name="decl_package_name" type="hidden" value="{{decl_package_name}}"></input>
              <input name="decl_word" type="hidden" value="{{decl_word}}"></input>
              create: <input class="create-word-link" name="name" type="text"></input>
            </form>
          </li>
        </ul>
      %end
    </ul>
  </td>
  <td id="name">{{word if word else ''}}
  </td>
</tr>
<tr>
  <td id="questions">
    %if questions:
      <form method="POST" action="/update_answers/{{package_dir}}/{{package_name}}/{{word}}">
        <table class="question-table">
          <tr>
            <th>Add</th>
            <th>Question</th>
            <th>Omit</th>
            <th>Answer</th>
          </tr>
          <tr>
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
    %end
  </td>
</tr>

<tr>
  <td id="text">
    %if text is not None:
      <form method="POST" action="/update_text/{{package_dir}}/{{package_name}}/{{word}}">
        <textarea name="text" rows="20" cols="80">{{text}}</textarea><br />
        <input type="submit" value="submit" id="submit-text">
      </form>
    %end
  </td>
</tr>

</table>
