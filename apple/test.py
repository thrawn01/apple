# Taken from eventlet wsgi_test.py
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


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


class TestBase( LimitedTestCase ):
    def setUp(self):
        LimitedTestCase.setUp( self )
        self.logfile = StringIO()
        self.site = DummySite()
        self.killer = None
        self.set_site()
        self.spawn_server()
        self.conn_class = httplib.HTTPConnection
        #self.conn_class = httplib.HTTPSConnection

    def tearDown(self):
        greenthread.kill(self.killer)
        eventlet.sleep(0)
        LimitedTestCase.tearDown( self )

    def connect( host='localhost', port=self.port ):
        self.connection = self.conn_class( host, port=port )

    def request( self, method='GET', path='/', data=[], headers={}, params={} ):
        try:
            self.connect()
            self.connection.request(method, path, data, headers)
            return self.connection.getresponse()
        except httplib.HTTPException:
            raise
        
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

    def set_site(self):
        raise NotImplementedError

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

