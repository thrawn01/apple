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

    def __call__(self, environ, start_response):
        log.debug( "Async.__call__" )
        eventlet_socket = environ['eventlet.input'].get_socket()
        socket = Socket( eventlet_socket, environ )
        # TODO: Do we really need this?
        status = '%d %s' % (response.status, HTTP_CODES[response.status])
        start_response(status, response.headerlist)

        self.handler( socket )
        return wsgi.ALREADY_HANDLED


class WebSocket( Async ):
    """ Provides a small wrapper for eventlet.WebSocketWSGI """

    def __init__( self, handler ):
        self.handler = handler
        def wrapper( ws ):
            class Wrapper( object ):
                def write( self, message ):
                    return ws.send( message )
                def read( self ):
                    return ws.wait( )
            return handler( Wrapper() )
        self.websocket = websocket.WebSocketWSGI( wrapper )
        
    def __call__(self, environ, start_response):
        return self.websocket(environ, start_response )
        

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
        
    def write( self, message):
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

        def handle(url, method):
            handler, args = self.match_url(url, method)
            if isinstance( handler, Async ):
                log.debug( "Async Call: %s(%s)" % (handler, args) )
                yield handler( environ, start_response )
            log.debug( "Calling: %s(%s)" % (handler, args) )

            #if isinstance( handler, websocket.WebSocketWSGI ):
                #log.debug( "Calling '%s' as WebSocketWSGI" % handler.handler.__name__ )
                #environ['apple.args'] = args
                #yield handler( environ, start_response )
            #else:
                #yield handler(**args)

        try:
            environ['bottle.app'] = self
            request.bind(environ)
            response.bind(self)
            result = handle(request.path, request.method)
            status = '%d %s' % (response.status, HTTP_CODES[response.status])

            # RFC2616 Section 4.3
            if response.status in (100, 101, 204, 304) or request.method == 'HEAD':
                start_response(status, response.headerlist)
                return []

            start_response(status, response.headerlist)
            return self._async_cast(result, request, response)

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

    def _async_cast(self, result, request, response):
        for value in result:
            return self._cast( value, request, response )


