import sys
import gevent.monkey # noqa: E402

patched = False

def patch():
    global patched
    if not patched:
        gevent.monkey.patch_all(thread=False)
        patched = True

def unpatch():
    import importlib # noqa: E402

    for x in sys.modules:
        try:
            importlib.reload(sys.modules[x])
        except NotImplementedError:
            pass

def with_unpatch(f):
    import functools # noqa: E402

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        unpatch()
        return f(*args, **kwargs)

    return wrapper
    