# server.py

from doctest_tools import setpath
setpath.setpath(__file__, remove_first = True)

from wsgiref.simple_server import make_server
import webbrowser
from ucc.web import wsgi_app

def run(port=8000):
    httpd = make_server('', port, wsgi_app.wsgi_app)
    print("Serving HTTP on port {}...".format(port))

    webbrowser.open('http://localhost:{}'.format(port), 2)

    # Respond to requests until process is killed
    httpd.serve_forever()

if __name__ == "__main__":
    run()
