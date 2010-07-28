from apple import Apple
from apple.test import TestBase

import unittest, sys, os, time, logging

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger( "test" )

apple = Apple()

@apple.route('/websocket')
@apple.websocket
def websocket( websocket ):
    socket.write( "Wait for it - " )
    result = socket.read()
    socket.write( "Hello World, I Got '%s'" % result )


@apple.route('/async')
@apple.async
def async( socket ):
    #result = sock.read()
    socket.write( "Wait for it - " )
    time.sleep(2)
    socket.write( "Hello World, Async" )


@apple.route('/apple')
def apple():
    yield "Wait for it - "
    time.sleep(2)
    yield "Hello World, Async with Yield"


class AppleTests( TestBase ):

    def setUp(self):
        TestBase.setUp(self)
        self.site = apple

    def tearDown(self):
        TestBase.tearDown(self)

    def testAsyncCall(self):
        response = self.request( method='GET', path='/async', params={} )

        for value in response:
            print "I Got '%s'" % value


