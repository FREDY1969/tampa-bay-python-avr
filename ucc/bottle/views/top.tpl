%rebase base title='Open Package', css_files=['top.css']

<ul class="package-dirs">
  %for packages_info in packages_dirs:
    %if packages_info.writable or packages_info.package_names:
      <li class="package-dir">{{packages_info.packages_name}}
        <ul class="packages">

          %for package in packages_info.package_names:
            <li class="package">
              <a class="open-package-link" href="/{{packages_info.packages_name}}/{{package}}">{{package}}</a>
            </li>
          %end

          %if packages_info.writable:
            <li class="create-package">
              create: <form class="create-form" method="POST" action="/create/{{packages_info.packages_name}}">
                <input name="name" class="create-input" type="text"></input>
              </form>
            </li>
          %end

        </ul>
      </li>
    %end
  %end
</ul>

