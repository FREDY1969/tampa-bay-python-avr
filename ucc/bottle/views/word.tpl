%rebase base title=package_name, css_files=['word.css']

<div class="menu">
  <a class="menu_item" href="/">Close</a>
  %if word is None:
    <a class="menu_item" href="/compile/{{packages_name}}/{{package_name}}">Compile</a>
    <a class="menu_item" href="/load/{{packages_name}}/{{package_name}}">Load</a>
  %else:
    <a class="menu_item" href="/compile/{{packages_name}}/{{package_name}}/{{word}}">Compile</a>
    <a class="menu_item" href="/load/{{packages_name}}/{{package_name}}/{{word}}">Load</a>
  %end
</div>

<table id="outer-table">
<col id="index-col"><col id="word-col">
<tr>
  <td id="contents" rowspan=3>
    <ul class="outer-contents">
      %for decl_packages_name, decl_package_name, decl_word, local_words in index:
        <li class="outer-element">
          <a class="decl-link" href="/{{decl_packages_name}}/{{decl_package_name}}/{{decl_word}}">
            {{decl_word}}
          </a>
        </li>
        <ul class="inner-contents">
          %for local_word in local_words:
            <li class="inner-element">
              <a class="word-link" href="/{{packages_name}}/{{package_name}}/{{local_word}}">
                {{local_word}}
              </a>
            </li>
          %end
          <li class="create-word-li">
            <form method="POST" action="/create_word/{{packages_name}}/{{package_name}}">
              <input name="decl_packages_name" type="hidden" value="{{decl_packages_name}}"></input>
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
      %include questions packages_name=packages_name, package_name=package_name, word=word, questions=questions
    %end
  </td>
</tr>

<tr>
  <td id="text">
    %if text is not None:
      <form method="POST" action="/update_text/{{packages_name}}/{{package_name}}/{{word}}">
        <textarea name="text" rows="20" cols="80">{{text}}</textarea><br />
        <input type="submit" value="submit" id="submit-text">
      </form>
    %end
  </td>
</tr>

</table>
