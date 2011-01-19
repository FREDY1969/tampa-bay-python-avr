<%!
    css_files = ['top.css']
%>
<%inherit file="base.tpl" />

<%def name="title()">
    Open Package
</%def>

<ul class="package-dirs">
  %for packages_info in packages_dirs:
    %if packages_info.writable or packages_info.package_names:
      <li class="package-dir">${packages_info.packages_name|h}
        <ul class="packages">

          %for package in packages_info.package_names:
            <li class="package">
              <a class="open-package-link" href="/view/${packages_info.packages_name|u}/${package|u}">${package|h}</a>
            </li>
          %endfor

          %if packages_info.writable:
            <li class="create-package">
              create: <form class="create-form" method="POST" action="/create/${packages_info.packages_name|u}">
                <input name="name" class="create-input" type="text"></input>
              </form>
            </li>
          %endif

        </ul>
      </li>
    %endif
  %endfor
</ul>

