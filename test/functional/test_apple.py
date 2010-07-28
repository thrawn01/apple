from apple import Apple
from apple.test import TestBase

import unittest, sys, os, time, logging

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


class AppleTests( TestBase ):

    def setUp(self):
        self.site = wsgi.default_app()

    def tearDown(self):
        pass

    def testAsyncCall(self):
        response = self.request( method='GET', path='/async', params={} )

        for value in response:
            print "I Got '%s'" % value


