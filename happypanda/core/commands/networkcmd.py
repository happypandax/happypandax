import attr
import requests
import cachecontrol
import os
import arrow

from happypanda.common import (hlogger, exceptions, constants, config)
from happypanda.core.command import CoreCommand, Command
from happypanda.core.commands import io_cmd
from happypanda.interface import enums

log = hlogger.Logger(constants.log_ns_network + __name__)


class Method(enums._APIEnum):
    GET = "get"
    POST = "post"
    PUT = "put"
    DELETE = "delete"
    HEAD = "head"
    OPTIONS = "options"


@attr.s
class RequestProperties:
    """

    Args:
        session: True for default session, False for no session, or custom session
    """

    method = attr.ib(default=None)
    output = attr.ib(default="")
    name = attr.ib(default="")  # for logging
    session = attr.ib(default=True)
    timeout = attr.ib(default=None)
    proxy = attr.ib(default=None)
    headers = attr.ib(default=None)
    files = attr.ib(default=None)
    data = attr.ib(default=None)
    json = attr.ib(default=None)
    params = attr.ib(default=None)
    auth = attr.ib(default=None)
    cookies = attr.ib(default=None)
    stream = attr.ib(default=False)
    stream_callback = attr.ib(default=None)
    progress = attr.ib(default=False)


class Response(CoreCommand):
    """
    """

    def __init__(self, _url, _request_method, _request_kwargs, _props):
        super().__init__()
        self.properties = _props
        self._method = _request_method
        self._kwargs = _request_kwargs
        self._rsp = None
        self._url = _url

    def _call(self):
        self._rsp = self._method(self._url, **self._kwargs)

    @property
    def response(self):
        "Underlying response object"
        return self._rsp

    @property
    def json(self):
        return self._rsp.json()

    @property
    def text(self):
        return self._rsp.text

    def save(self, filepath, decode_unicode=False, extension=False):
        """
        Save the content to a file. Also accepts CoreFS.

        Args:
            extension: append file extension from url to filepath

        Returns str path to file
        """
        assert isinstance(filepath, (str, io_cmd.CoreFS))
        log.i("Saving content to file", self._rsp.url)
        if isinstance(filepath, str):
            filepath = io_cmd.CoreFS(filepath)

        if extension:
            filepath = io_cmd.CoreFS(filepath.path + io_cmd.CoreFS(os.path.split(self._url)[1]).ext, filepath._archive)

        self.set_max_progress(int(self._rsp.headers.get('Content-Length', '0').strip()) + 1)
        self.set_progress(type_=enums.ProgressType.Request)
        log.d("Saving to filepath", filepath)
        with filepath.open(mode="wb") as f:
            if self.properties.stream:
                s_time = arrow.now()
                dl_length = 0
                for data in self._rsp.iter_content(chunk_size=1024, decode_unicode=decode_unicode):
                    data_len = len(data)
                    dl_length += data_len
                    self.next_progress(
                        data_len, text="[{0:.3f} mbps] - {1}".format((dl_length / 1000000) / max((arrow.now() - s_time).seconds, 1), self._url))
                    f.write(data)
                    f.flush()
            else:
                raise NotImplementedError
        self.next_progress()
        return filepath.path


class _Request(Command):
    """
    """
    default_session = None

    def __init__(self, session=True, priority=constants.Priority.Low):
        super().__init__(priority)
        if not _Request.default_session:
            _Request.default_session = constants.internaldb.network_session.get(
                cachecontrol.CacheControl(requests.Session()))
            self.default_session = _Request.default_session

        if session in (True, None):
            self.session = self.default_session
        elif isinstance(session, requests.Session):
            self.session = session
        else:
            self.session = requests

    def request(self, url, props):
        assert isinstance(props, RequestProperties)
        if not props.method:
            raise exceptions.NetworkError("No valid HTTP method", props)
        verb = Method.get(props.method)  # TODO: wrap exceptions raised by APIEnum
        method = {
            'get': self.session.get,
            'post': self.session.post,
            'delete': self.session.delete,
            'put': self.session.put,
            'head': self.session.head,
            'options': self.session.options,
        }.get(verb.value)
        kwargs = {}
        kwargs['timeout'] = props.timeout or config.request_timeout.value
        if props.headers is not None:
            kwargs['headers'] = props.headers
        if props.files is not None:
            kwargs['files'] = props.files
        if props.data is not None:
            kwargs['data'] = props.data
        if props.params is not None:
            kwargs['params'] = props.params
        if props.auth is not None:
            kwargs['auth'] = props.auth
        if props.cookies is not None:
            kwargs['cookies'] = props.cookies
        if props.json is not None:
            kwargs['json'] = props.json
        if props.stream and verb == Method.GET:
            kwargs['stream'] = props.stream
        r = Response(url, method, kwargs, props)
        r.merge_progress_into(self)
        r._call()
        return r

    def cleanup_session(self):
        constants.internaldb.network_session.set(self.default_session)


class SimpleRequest(_Request):
    """
    """

    def __init__(self, url, properties):
        assert isinstance(properties, RequestProperties)
        assert isinstance(url, str)
        super().__init__(properties.session)
        self.url = url
        self.properties = properties

    def main(self):
        return self.request(self.url, self.properties)


class SimpleGETRequest(SimpleRequest):
    """
    A convenience wrapper around SimpleRequest for GET requests
    """

    def __init__(self, url, properties=RequestProperties(), **kwargs):
        properties.method = Method.GET
        return super().__init__(url, properties, **kwargs)


class SimplePOSTRequest(SimpleRequest):
    """
    A convenience wrapper around SimpleRequest for POST requests
    """

    def __init__(self, url, properties=RequestProperties(), **kwargs):
        properties.method = Method.POST
        return super().__init__(url, properties, **kwargs)


class MultiRequest(_Request):
    """
    """

    def __init__(self, urls, properties):
        assert isinstance(properties, RequestProperties)
        assert isinstance(urls, (tuple, list, set, dict))
        super().__init__(properties.session)
        self.properties = properties


class MultiGETRequest(MultiRequest):
    """
    A convenience wrapper around MultiRequest for GET requests
    """

    def __init__(self, url, properties=RequestProperties(), **kwargs):
        properties.method = Method.GET
        return super().__init__(url, properties, **kwargs)


class MultiPOSTRequest(MultiRequest):
    """
    A convenience wrapper around MultiRequest for POST requests
    """

    def __init__(self, url, properties=RequestProperties(), **kwargs):
        properties.method = Method.POST
        return super().__init__(url, properties, **kwargs)
