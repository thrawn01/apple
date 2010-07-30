from apple import Apple
from apple.test import TestBase
import unittest, sys, os, time, logging

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger( "test" )

apple = Apple()

@apple.route('/websocket')
@apple.websocket
def websocket( websocket ):
    websocket.write( "Wait for it - " )
    result = websocket.read()
    websocket.write( "Hello World, I Got '%s'" % result )

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

    def set_site(self):
        self.site = apple

    def testAsyncCall(self):
        response = self.request( method='GET', path='/async', params={} )
        self.assertEquals( response.status, 200 )
        self.assertEquals( response.read(), "Wait for it - Hello World, Async" )

    def testWebSocket(self):
        response = self.request( method='WEBSOCK', path='/websocket', params={} )
        #self.assertEquals( response.status, 101 )
        response.write( "Testing" )
        self.assertEquals( response.read(), "Wait for it - " )
        self.assertEquals( response.read(), "Hello World, I Got 'Testing'" )

