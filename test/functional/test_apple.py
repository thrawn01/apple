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
    socket.write( "Hello World, Async" )


@apple.route('/helloworld')
def helloworld():
    yield "Wait for it - "
    yield "Hello World, Async with Yield"


class AppleTests( TestBase ):

    def setUp(self):
        self.site = apple
        TestBase.setUp(self)

    def tearDown(self):
        TestBase.tearDown(self)

    def testAsyncCall(self):
        response = self.request( method='GET', path='/async', params={} )
        self.assertEquals( response.status, 200 )
        self.assertEquals( response.read(), "Wait for it - Hello World, Async" )

