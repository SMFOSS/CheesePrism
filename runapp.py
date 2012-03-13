import os

from paste.deploy import loadapp
from paste.script.cherrypy_server import cpwsgi_server

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    wsgi_app = loadapp('config:production.ini', relative_to='.')
    cpwsgi_server(wsgi_app, host='0.0.0.0', port=port,
                  numthreads=10, request_queue_size=200)
