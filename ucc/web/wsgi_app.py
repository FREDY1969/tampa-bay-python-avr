# wsgi_app.py

# Possibly interesting values:
#     CONTENT_LENGTH:
#     CONTENT_TYPE: application/x-www-form-urlencoded
#     PATH_INFO: /hello/mom/and/dad.html
#     QUERY_STRING: this=value&that=too
#     REMOTE_ADDR: 127.0.0.1
#     REQUEST_METHOD: GET
#     SCRIPT_NAME:
#     wsgi.errors: <file>
#     wsgi.file_wrapper: <file>
#     wsgi.input: <file to read request body>
#     wsgi.multiprocess: False
#     wsgi.multithread: True
#     wsgi.run_once: False

import os
import urllib.parse
import json

from ucc.web import session

Debug = 0

Web_framework_dir = os.path.join(os.path.dirname(__file__), "media")

Content_types = {
    'html': 'text/html',
    'js': 'text/javascript',
    'css': 'text/css',
    'gif': 'image/gif',
    'png': 'image/png',
    'jpeg': 'image/jpeg',
    'jpg': 'image/jpeg',
}

Module_cache = {}

Session = session.session()

def import_(modulename):
    ''' modulepath does not include .py
    '''
    if Debug: print("import_:", modulename, file=sys.stderr)
    mod = __import__(modulename)
    for comp in modulename.split('.')[1:]:
        mod = getattr(mod, comp)
    return mod

def wsgi_app(environ, start_response):
    global Module_cache

    # Parse the path:
    path = environ["PATH_INFO"].lstrip('/')
    components = path.split('/')

    if len(components) != 3 or components[0] != 'ajax':
        if not path:
            path = 'index.html'
        full_path = os.path.join(Web_framework_dir, path)
        suffix = path.rsplit('.', 1)[1]
        try:
            try:
                data = __loader__.get_data(full_path)
            except NameError:
                with open(full_path, 'rb') as f:
                    data = f.read()
            start_response("200 OK", [('Content-Type', Content_types[suffix])])
            return [data]
        except IOError:
            start_response("404 Not Found", [])
            return []

    # else AJAX call...

    modulepath, fn_name = components[1:]

    if modulepath not in Module_cache:
        Module_cache[modulepath] = import_('ucc.web.' + modulepath)

    if environ["REQUEST_METHOD"] == "GET":
        query_string = environ["QUERY_STRING"]
    else:
        post_data = environ['wsgi.input'].read(int(environ['CONTENT_LENGTH']))
        query_string = post_data.decode('utf-8')
    data = urllib.parse.parse_qs(query_string)['data'][0]

    # "200 OK", [('header_field_name', 'header_field_value')...], data
    status, headers, document = \
      getattr(Module_cache[modulepath], fn_name)(Session, **json.loads(data))
    headers.append(('Content-Type', 'application/json'))
    start_response(status, headers)
    return [json.dumps(document)]

