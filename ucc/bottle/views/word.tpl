<%!
    css_files = ['word.css']
%>
<%inherit file="base.tpl" />

<%def name="title()">
    ${package.package_label}
</%def>

<div class="menu">
  <a class="menu-item" href="/">Close</a>
  %if word is None:
    <a class="menu-item" href="/compile/${packages_name|u}/${package_name|u}">Compile</a>
    <a class="menu-item" href="/load/${packages_name|u}/${package_name|u}">Load</a>
  %else:
    <a class="menu-item" href="/compile/${packages_name|u}/${package_name|u}/${word|u}">Compile</a>
    <a class="menu-item" href="/load/${packages_name|u}/${package_name|u}/${word|u}">Load</a>
  %endif
</div>

<div id="contents">
  <ul class="outer-contents">
    %for decl_packages_name, decl_package_name, decl_word, local_words in index:
      %if local_words:
        <li class="outer-element">
          <a class="decl-link" href="/view/${decl_packages_name|u}/${decl_package_name|u}/${decl_word.name|u}">
            ${decl_word.label|h}
          </a>
        </li>
        <ul class="inner-contents">
          %for local_word in local_words:
            <li class="inner-element">
              <a class="word-link" href="/view/${packages_name|u}/${package_name|u}/${local_word.name|u}">
                ${local_word.label|h}
              </a>
            </li>
          %endfor

        </ul>
      %endif
    %endfor
  </ul>
  <form class="create-word-form" method="POST" action="/create_word/${packages_name|u}/${package_name|u}">
    <div class="create-word">
      create word:
      <select class="create-word-decl" name="decl" size="1">
        %for decl_packages_name, decl_package_name, decl_word, local_words in index:
          <option value="${decl_packages_name|h}.${decl_package_name|h}.${decl_word.name|h}">
            ${decl_word.label|h}
          </option>
        %endfor
      </select>
      <input class="create-word-name" name="name" type="text">
    </div>
  </form>
</div>

<div id="right-column">
  <div id="name">${(word_word.label if word_word else '')|h}</div>

  <div id="questions">
    %if word_word is not None and word_word.has_questions():
      <%include file="questions.tpl" />
    %endif
  </div>

  <div id="text">
    %if word_word is not None and word_word.has_text():
      <form method="POST" action="/update_text/${packages_name|u}/${package_name|u}/${word|u}">
        <textarea id="textarea" name="text" rows="20" cols="80">${word_word.get_text()|h}</textarea><br />
        <input id="submit-text" type="submit" value="submit">
      </form>
    %endif
  </div>
</div>
