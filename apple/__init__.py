from bottle import Bottle, request, response, tob, HTTP_CODES, HTTPResponse
from traceback import format_exc
import logging, sys, pdb, types

import eventlet
from eventlet import websocket
from eventlet import semaphore
from eventlet import wsgi
from eventlet.green import socket

log = logging.getLogger("apple")

class Async( object ):
    def __init__( self, handler ):
        self.handler = handler

    def __call__( self, environ, start_response, args ):
        start_response( '%d %s' % ( response.status, HTTP_CODES[response.status] ), response.headerlist )
        args['socket'] = Socket( environ['eventlet.input'].get_socket(), environ )
        self.handler( **args )
        return wsgi.ALREADY_HANDLED


class WebSocket( Async ):
    """ Provides a small wrapper for eventlet.WebSocketWSGI """

    def __init__( self, handler ):
        self.handler = handler
        def wrapper( ws ):
            class Wrapper( object ):
                def send( self, message ):
                    return ws.send( message )

                def recv( self ):
                    return ws.wait()

            return handler( Wrapper() )
        self.websocket = websocket.WebSocketWSGI( wrapper )
        
    def __call__( self, environ, start_response, args ):
        return self.websocket( environ, start_response )
        

class Socket( object ):
    def __init__( self, socket, environ ):
        self.socket = socket
        self.origin = environ.get('HTTP_ORIGIN')
        self.path = environ.get('PATH_INFO')
        self.lock = semaphore.Semaphore()
   
    def read( self, length ):
        result = self.socket.recv( length )
        if result == '':
            return None
        return result
        
    def write( self, message ):
        self.lock.acquire()
        try:
            return self.socket.sendall( message )
        finally:
            self.lock.release()


class Apple(Bottle):
    """ WSGI application """
    async = Async
    websocket = WebSocket

    def __init__(self, autojson=True, config=None):
        Bottle.__init__(self, autojson=False, config=config )
        self.catchall = False

    def __call__(self, environ, start_response):
        """ Apple WSGI-interface. """

        try:
            environ['bottle.app'] = self
            request.bind(environ)
            response.bind(self)
            handler, args = self.match_url(request.path, request.method)
            # If its a Websocket or Async call
            if isinstance( handler, Async ):
                return handler( environ, start_response, args )

            result = handler( **args )
            status = '%d %s' % (response.status, HTTP_CODES[response.status])
            start_response(status, response.headerlist)
            # RFC2616 Section 4.3
            if response.status in (100, 101, 204, 304) or request.method == 'HEAD':
                return []

            socket = Socket( environ['eventlet.input'].get_socket(), environ )
            for value in iter(result):
                socket.write( self._cast( value, request, response ) )

            return []

        except (KeyboardInterrupt, SystemExit):
            raise
        except HTTPResponse, e:
            start_response( '%s %s' % (e.status, HTTP_CODES[e.status]), [('Content-Type', 'text/html')] )
            return e
        except Exception, e:
            message = "Un-Caught execption '%s' PATH '%s' " % (repr(e), environ.get('PATH_INFO', '/'))
            log.error( message )
            log.error( "%s" % format_exc() )

            # Tell the WSGI server about the error
            environ['wsgi.errors'].write( message )
            
            # Let the client know there was an internal error
            start_response( '%s %s' % (500, HTTP_CODES[500]), [('Content-Type', 'text/html')] )
            return [tob( '500 %s - Un-Caught exception, Check server logs for stacktrace' % HTTP_CODES[500] ) ]


