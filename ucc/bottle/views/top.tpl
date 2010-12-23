%rebase base title='Open Package', css_files=['top.css']

<ul class="package-dirs">
  %for package_dir, packages in package_dirs:
    <li class="package-dir">{{package_dir}}
      (create: <form class="create-form" method="POST" action="/create/{{package_dir}}">
        <input name="name" class="create-input" type="text"></input>
      </form>)
      <ul class="packages">
        %for package in packages:
          <li class="package">
            <a class="open-package-link" href="/{{package_dir}}/{{package}}">{{package}}</a>
          </li>
        %end
      </ul>
    </li>
  %end
</ul>

