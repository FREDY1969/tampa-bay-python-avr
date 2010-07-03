# server.py

"""Functions for controlling a WSGI application server"""

import webbrowser
from wsgiref.simple_server import make_server

WSGI_SERVER = None

def start(app, host='', port=8005):
    """Start the WSGI application."""
    WSGI_SERVER = make_server(host, port, app)
    url = 'http://{server_name}:{server_port}/'.format(**WSGI_SERVER.__dict__)
    print("Serving WSGI application on {}...".format(url))
    webbrowser.open(url, 2)
    WSGI_SERVER.serve_forever()

def stop():
    """Stop the WSGI application."""
    if WSGI_SERVER is not None:
        WSGI_SERVER.shutdown()
