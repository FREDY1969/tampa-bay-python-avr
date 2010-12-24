<!DOCTYPE html>
<html>
<head>
  <META http-equiv="Content-Type" content="text/html; charset=utf-8">
  <title>${self.title()|h}</title>
  %for css_file in self.attr.css_files:
    <link rel="stylesheet" href="/static/css/${css_file|u}" type="text/css" media="screen" charset="utf-8">
  %endfor
</head>
<body>
  ${next.body()}
</body>
</html>
