# server.py

from doctest_tools import setpath
setpath.setpath(__file__, remove_first = True)

from ucc.web import wsgi_app
from wsgiref.simple_server import make_server

httpd = make_server('', 8000, wsgi_app.wsgi_app)
print "Serving HTTP on port 8000..."

# Respond to requests until process is killed
httpd.serve_forever()
