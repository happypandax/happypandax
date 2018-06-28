import sys
import gevent.monkey

patched = False


def _patched_os_read(f, timeout=5):
    def wrapper(*args, **kwargs):
        class A:
            pass
        r = A
        err = None
        import gevent  # noqa: E402
        with gevent.Timeout(timeout, False):
            while True:
                try:
                    r = f(*args, **kwargs)
                    break
                except BlockingIOError as e:
                    err = e
                    gevent.sleep(0.1)

        if r is A and err:
            raise err
        elif r is A:
            r = None
        return r
    return wrapper


def patch():
    global patched
    if not patched:
        gevent.monkey.patch_all(thread=False, socket=False)
        import os  # noqa: E402
        from multiprocessing import managers, connection  # noqa: E402
        if os.name == "posix":
            # multiprocessing.Manager spawns socketlisteners in a nativethread which causes
            # "cannot switch to a different thread" errors when using a monkeypatched socket
            # so we just let it use the native socket instead
            import socket  # noqa: E402
            connection.socket = socket
            del sys.modules[socket.__name__]
        gevent.monkey.patch_socket()
        # os.read = _patched_os_read(os.read) not necessary atm
        managers.Server.accepter = make_gevent_compatible_in_native_thread(managers.Server.accepter)
        managers.Server.handle_request = make_gevent_compatible_in_native_thread(managers.Server.handle_request)
        patched = True


def unpatch():
    import importlib  # noqa: E402

    for x in sys.modules:
        try:
            importlib.reload(sys.modules[x])
        except NotImplementedError:
            pass


def with_unpatch(f):
    import functools  # noqa: E402

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        unpatch()
        return f(*args, **kwargs)

    return wrapper


def make_gevent_compatible_in_native_thread(f):
    import gevent  # noqa: E402
    import threading  # noqa: E402

    def _daemon():
        while True:
            gevent.sleep(0.1)

    def wrapper(*args, **kwargs):
        l = threading.local()
        g = None
        if not getattr(l, "_daemon", False):
            gevent.get_hub()
            g = l._daemon = gevent.spawn(_daemon)
        r = None
        try:
            r = f(*args, **kwargs)
        finally:
            if g is not None:
                g.kill()
        return r

    return wrapper


original_thread_cls = None


def patch_native_thread():
    global original_thread_cls

    import threading  # noqa: E402

    if not original_thread_cls:
        original_thread_cls = threading.Thread

    class GeventNativeThread(threading.Thread):

        def __init__(self, *args, **kwargs):
            target = kwargs.get("target", None)
            if target:
                kwargs['target'] = make_gevent_compatible_in_native_thread(target)
            super().__init__(*args, **kwargs)

    threading.Thread = GeventNativeThread


def unpatch_native_thread():
    global original_thread_cls
    import threading  # noqa: E402

    if original_thread_cls:
        threading.Thread = original_thread_cls
