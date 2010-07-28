#! /usr/bin/env python

import eventlet, sys
from bottle import Bottle, run
from apple import Apple
import logging
import time

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger( "test" )

wsgi = Apple()

@wsgi.route('/websocket')
@wsgi.websocket
def websocket( websocket ):
    socket.write( "Wait for it - " )
    result = socket.read()
    socket.write( "Hello World, I Got '%s'" % result )


@wsgi.route('/async')
@wsgi.async
def async( socket ):
    #result = sock.read()
    socket.write( "Wait for it - " )
    time.sleep(2)
    socket.write( "Hello World, Async" )


@wsgi.route('/apple')
def apple():
    yield "Wait for it - "
    time.sleep(2)
    yield "Hello World, Async with Yield"


if __name__ == "__main__":
    run(app=wsgi, host='thrawn01.org', port=8080)

