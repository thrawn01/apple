from bottle import Bottle, request, response, tob
from traceback import format_exc
import logging from logging


class Apple(Bottle):
    """ WSGI application """

    def __init__(self, autojson=True, config=None):
        Bottle.__init__(self, autojson=False, config=config )

        # Setup logging
        self.log = logging.getlogger("Apple")


    def handle(self, url, method):
        if not self.serve:
            return HTTPError(503, "Server stopped")

        try:
            handler, args = self.match_url(url, method)
            # Call the matching method
            return handler(**args)

        except HTTPResponse, e:
            return e

    def __call__(self, environ, start_response):
        """ Apple WSGI-interface. """

        try:
            # Tell the WSGI environ about us
            environ['bottle.app'] = self
            request.bind(environ)
            response.bind(self)
            # Execute the method
            out = self.handle(request.path, request.method)
            # Convert the output into somthing wsgi understands
            out = self._cast(out, request, response)
            # rfc2616 section 4.3
            if response.status in (100, 101, 204, 304) or request.method == 'HEAD': out = []
            status = '%d %s' % (response.status, HTTP_CODES[response.status])
            # Report the status of the call
            start_response(status, response.headerlist)
            # Return the result of the call
            return out

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception, e:
            message = "Un-Caught execption '%s' PATH '%s'" % (repr(e), environ.get('PATH_INFO', '/'))
            # Log the error
            self.log.error( messge )
            # Tell the WSGI server about the error
            environ['wsgi.errors'].write( message )
            
            # Let the client know there was an internal error
            start_response('500 INTERNAL SERVER ERROR', [('Content-Type', 'text/html')])
            return [tob('Un-Caught exception, Check server logs for stacktrace')]


