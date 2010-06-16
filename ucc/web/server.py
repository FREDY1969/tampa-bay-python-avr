# server.py

from doctest_tools import setpath
setpath.setpath(__file__, remove_first = True)

from wsgiref.simple_server import make_server
import webbrowser
from ucc.web.wsgi_app import wsgi_app

def start(port=8005):
    httpd = make_server('', port, wsgi_app)
    print("Serving HTTP on port {}...".format(port))
    
    webbrowser.open('http://localhost:{}'.format(port), 2)
    
    # Respond to requests until process is killed
    httpd.serve_forever()
