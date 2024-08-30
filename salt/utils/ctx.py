import contextlib

try:
    # Try the stdlib C extension first
    import _contextvars as contextvars
except ImportError:
    # Py<3.7
    import contextvars

DEFAULT_CTX_VAR = "request_ctxvar"
request_ctxvar = contextvars.ContextVar(DEFAULT_CTX_VAR)


@contextlib.contextmanager
def request_context(data):
    """
    A context manager that sets and un-sets the loader context
    """
    tok = request_ctxvar.set(data)
    try:
        yield
    finally:
        request_ctxvar.reset(tok)


def get_request_context():
    return request_ctxvar.get({})


class RequestContext:
    """
    A context manager that saves some per-thread state globally.
    Intended for use with Tornado's StackContext.
    https://gist.github.com/simon-weber/7755289
    Simply import this class into any module and access the current request handler by this
    class's class method property 'current'. If it returns None, there's no active request.
    .. code:: python
        from raas.utils.ctx import RequestContext
        current_request_handler = RequestContext.current
    """

    _state = threading.local()
    _state.current_request = {}

    def __init__(self, current_request):
        self._current_request = current_request

    @ClassProperty
    @classmethod
    def current(cls):
        if not hasattr(cls._state, "current_request"):
            return {}
        return cls._state.current_request

    def __enter__(self):
        self._prev_request = self.__class__.current
        self.__class__._state.current_request = self._current_request

    def __exit__(self, *exc):
        self.__class__._state.current_request = self._prev_request
        del self._prev_request
        if self.__class__._state.current_request == {}:
            # If we're back to an empty dict, explicitly clear to help GC
            try:
                del self.__class__._state.current_request
            except AttributeError:
                pass
        return False

    def __call__(self):
        return self
