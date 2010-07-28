#! /usr/bin/env python

import eventlet, sys
from bottle import Bottle, run
from apple import Apple
import logging
import time

#from eventlet import websocket
#@websocket.WebSocketWSGI

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger( "test" )

wsgi = Apple()

@wsgi.route('/websocket')
@wsgi.websocket
def websocket(ws):
    args = ws.environ['apple.args']
    return "Hello World, with WebSockets"

@wsgi.route('/async')
@wsgi.async
def async( sock ):
    #result = sock.read()
    sock.write( "Wait for it - " )
    time.sleep(2)
    sock.write( "Hello World, Async" )

@wsgi.route('/apple')
def apple():
    yield "Wait for it - "
    time.sleep(2)
    yield "Hello World, Async with Yield"


if __name__ == "__main__":
    run(app=wsgi, host='thrawn01.org', port=8080)

