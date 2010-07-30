# Taken from eventlet wsgi_test.py
import unittest, eventlet, logging, sys, urllib, socket
from eventlet.green import urllib2
from eventlet.green import httplib
from eventlet.websocket import WebSocket, WebSocketWSGI
from eventlet import wsgi
from eventlet import event
from eventlet import greenthread
from eventlet import debug, hubs

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger( "apple.test" )

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

class TestIsTakingTooLong( Exception ):
    pass

class NotImplemented( Exception ):
    pass


class LimitedTestCase(unittest.TestCase):
    """ Unittest subclass that adds a timeout to all tests.  Subclasses must
    be sure to call the LimitedTestCase setUp and tearDown methods.  The default
    timeout is 1 second, change it by setting self.TEST_TIMEOUT to the desired
    quantity."""

    TEST_TIMEOUT = 1
    def setUp(self):
        import eventlet
        self.timer = eventlet.Timeout(self.TEST_TIMEOUT,
                                      TestIsTakingTooLong(self.TEST_TIMEOUT))

    def reset_timeout(self, new_timeout):
        """Changes the timeout duration; only has effect during one test case"""
        import eventlet
        self.timer.cancel()
        self.timer = eventlet.Timeout(new_timeout,
                                      TestIsTakingTooLong(new_timeout))

    def tearDown(self):
        log.debug( "LimitedTestCase::tearDown()" )
        self.timer.cancel()
        try:
            hub = hubs.get_hub()
            num_readers = len(hub.get_readers())
            num_writers = len(hub.get_writers())
            assert num_readers == num_writers == 0
        except AssertionError, e:
            print "ERROR: Hub not empty"
            print debug.format_hub_timers()
            print debug.format_hub_listeners()


def hello_world(env, start_response):
    if env['PATH_INFO'] == 'notexist':
        start_response('404 Not Found', [('Content-type', 'text/plain')])
        return ["not found"]

    start_response('200 OK', [('Content-type', 'text/plain')])
    return ["hello world"]


class DummySite(object):
    def __init__(self):
        self.application = hello_world

    def __call__(self, env, start_response):
        return self.application(env, start_response)


class WebSocketResponse( object ):
    def __init__(self, sock ):
        resp = httplib.HTTPResponse( sock, method='GET' )
        resp.begin()
        self.status = resp.status
        environ = { 
            'HTTP_ORIGIN': resp.getheader( 'HTTP_ORIGIN', '' ),
            'HTTP_WEBSOCKET_PROTOCOL': resp.getheader( 'HTTP_WEBSOCKET_PROTOCOL', '' ),
            'PATH_INFO': resp.getheader( 'PATH_INFO', '' ) }
        self.sock = WebSocket( sock=sock, environ=environ, version=0 )

    def write( self, message ):
        result = self.sock.send( message )
        eventlet.sleep(0.001)
        return result

    def read( self ):
        result = self.sock.wait()
        eventlet.sleep(0.001)
        return result

    def close( self ):
        sock.close()
        eventlet.sleep(0.01)


class TestBase( LimitedTestCase ):

    def setUp(self):
        log.debug( "setUp()" )
        LimitedTestCase.setUp( self )
        self.logfile = StringIO()
        self.killer = None
        self.host = 'localhost'
        self.conn_class = httplib.HTTPConnection
        #self.conn_class = httplib.HTTPSConnection
        self.set_site()
        self.spawn_server()

    def tearDown(self):
        log.debug( "TestBase::tearDown()" )
        greenthread.kill(self.killer)
        eventlet.sleep(0)
        LimitedTestCase.tearDown( self )

    def connect( self, host='localhost' ):
        log.debug( "Connecting '%s:%s'" % (host, self.port) )
        return self.conn_class( self.host, port=self.port )

    def request( self, method='GET', path='/', data=[], headers={}, params={} ):
        if method == "WEBSOCK":
            return self.websocket_request( path, data, headers, params )
        try:
            self.connection = self.connect()
            # TODO: Encode params in url
            self.connection.request(method, path, data, headers)
            return self.connection.getresponse()
        except httplib.HTTPException:
            raise
    
    def websocket_request( self, path='/', data=[], headers={}, params={} ):
        request_header = ( "GET %s?%s HTTP/1.1" % ( path, urllib.urlencode( params ) ) )
        origin = "Origin: http://localhost:%s" % self.port
        headers = [
                request_header,
                "Upgrade: WebSocket",
                "Connection: Upgrade",
                "Host: localhost:%s" % self.port,
                origin,
                "WebSocket-Protocol: ws", ]

        sock = eventlet.connect( ( 'localhost', self.port ) )
        sock.sendall( '\r\n'.join( headers ) + '\r\n\r\n' )

        #first_resp = sock.recv( 1024 )
        #log.debug( "WebSocket Resp: %s" % first_resp )
        #return WebSocketResponse( int( first_resp.split(' ')[1] ) )

        return WebSocketResponse( sock )

    def spawn_server(self, **kwargs):
        """Spawns a new wsgi server with the given arguments.
        Sets self.port to the port of the server, and self.killer is the greenlet
        running it.

        Kills any previously-running server."""
        eventlet.sleep(0) # give previous server a chance to start
        if self.killer:
            greenthread.kill(self.killer)
            eventlet.sleep(0) # give killer a chance to kill

        new_kwargs = dict(max_size=128,
                          log=self.logfile,
                          site=self.site)
        new_kwargs.update(kwargs)

        if 'sock' not in new_kwargs:
            new_kwargs['sock'] = eventlet.listen(('localhost', 0))

        self.port = new_kwargs['sock'].getsockname()[1]
        self.killer = eventlet.spawn_n(
            wsgi.server,
            **new_kwargs)
        log.debug( "Server Spawned '%s:%s'" % ('localhost', self.port) )

    def assert_less_than(self, a,b,msg=None):
        if msg:
            self.assert_(a<b, msg)
        else:
            self.assert_(a<b, "%s not less than %s" % (a,b))

    assertLessThan = assert_less_than

    def assert_less_than_equal(self, a,b,msg=None):
        if msg:
            self.assert_(a<=b, msg)
        else:
            self.assert_(a<=b, "%s not less than or equal to %s" % (a,b))

    assertLessThanEqual = assert_less_than_equal

    def set_site( self ):
        raise NotImplemented()

