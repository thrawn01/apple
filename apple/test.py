#! /usr/bin/env python

import eventlet
from bottle import Bottle, run

wsgi = Bottle()
wsgi.catchall = False

@wsgi.route('/hello')
def hello():
    return "From Bottle, Hello World ( My first Web Service )"

if __name__ == "__main__":
    run(app=wsgi, host='thrawn01.org', port=8080)

