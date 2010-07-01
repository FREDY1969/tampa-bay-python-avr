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

"""WSGI application to handle media and AJAX requests.

AJAX requests folow the format:

    /ajax/{module}/{handler}?data={json_payload}

Response to AJAX requests are either blank or JSON.

Media requests are any static file that is not an AJAX call.

"""

import os
import sys
import urllib.parse
import json

import ucc.web.session

DEBUG = 1
MEDIA_DIR = os.path.join(os.path.dirname(__file__), "media")
CONTENT_TYPES = {
    'html': 'text/html',
    'js': 'text/javascript',
    'css': 'text/css',
    'gif': 'image/gif',
    'png': 'image/png',
    'jpeg': 'image/jpeg',
    'jpg': 'image/jpeg',
}

module_cache = {}
session = ucc.web.session.Session()

def import_(modulename):
    """Import and return modulename."""
    if DEBUG: print("import_:", modulename, file=sys.stderr)
    mod = __import__(modulename)
    for comp in modulename.split('.')[1:]:
        mod = getattr(mod, comp)
    return mod

def wsgi_app(environ, start_response):
    """Return requested media or respond to ajax request."""

    path, components = parse_path(environ["PATH_INFO"])

    if components[0] == 'ajax' and len(components) == 3:
        status, headers, document = ajax_dispatch(path, components, environ)
    else:
        status, headers, document = media_dispatch(path, components, environ)
    
    start_response(status, headers)
    return document

def parse_path(path):
    """Clean path, parse it into a / delimited list and return both."""
    path = path.strip('/')
    components = path.split('/')
    return path, components

def parse_qs(query_string):
    """Parse query_string into dict of values."""
    data = urllib.parse.parse_qs(query_string, True)
    for key in data:
        if len(data[key]) == 1:
            data[key] = data[key][0]
    return data

def media_dispatch(path, components, environ):
    if not path:
        path = 'index.html'
    full_path = os.path.join(MEDIA_DIR, path)
    suffix = path.rsplit('.', 1)[1]
    try:
        try:
            data = __loader__.get_data(full_path)
        except NameError:
            with open(full_path, 'rb') as f:
                data = f.read()
        return "200 OK", [('Content-Type', CONTENT_TYPES[suffix])], [data]
    except IOError:
        return "404 Not Found", [], []

def ajax_dispatch(path, components, environ):
    global module_cache
    modulepath, fn_name = components[1:]

    if modulepath not in module_cache:
        module_cache[modulepath] = import_("ucc.web.ajax." + modulepath)
        
    if environ["REQUEST_METHOD"] == "GET":
        query_string = environ["QUERY_STRING"]
    else:
        post_data = environ['wsgi.input'].read(int(environ['CONTENT_LENGTH']))
        query_string = post_data.decode('utf-8')
    data = parse_qs(query_string)

    status, headers, document = \
                   getattr(module_cache[modulepath], fn_name)(session, data)
    headers.append(('Content-Type', 'application/json'))
    # "200 OK", [('header_field_name', 'header_field_value')...], data
    return status, headers, [json.dumps(document)]
