"""
.Network
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. autoclass:: happypanda.core.commands.network_cmd.Method
    :members:

.. autoclass:: happypanda.core.commands.network_cmd.RequestProperties
    :members:

"""

import attr
import requests
import cachecontrol
import os
import arrow
import typing

from happypanda.common import (hlogger, exceptions, constants, config)
from happypanda.core.command import CoreCommand, Command
from happypanda.core.commands import io_cmd
from happypanda.interface import enums

log = hlogger.Logger(constants.log_ns_network + __name__)


class Method(enums._APIEnum):

    #: GET
    GET = "get"
    #: POST
    POST = "post"
    #: PUT
    PUT = "put"
    #: DELETE
    DELETE = "delete"
    #: HEAD
    HEAD = "head"
    #: OPTIONS
    OPTIONS = "options"


@attr.s
class RequestProperties:
    #: a :class:`.Method` object
    method: Method = attr.ib(default=None)
    name: str = attr.ib(default="")  # for logging
    #: set to True for default session, False for no session, or to a custom session
    session: bool = attr.ib(default=True)
    #: request timeout
    timeout: int = attr.ib(default=None)
    #: proxy
    proxy = attr.ib(default=None)
    #: headers
    headers = attr.ib(default=None)
    #: files
    files = attr.ib(default=None)
    #: data
    data = attr.ib(default=None)
    #: json
    json = attr.ib(default=None)
    #: params
    params = attr.ib(default=None)
    #: auth
    auth = attr.ib(default=None)
    #: cookies
    cookies = attr.ib(default=None)
    #: stream
    stream = attr.ib(default=False)
    #: stream_callback
    stream_callback = attr.ib(default=None)
    #: progress
    progress = attr.ib(default=False)


class Response(CoreCommand):
    """
    A request response. Not meant to be instanced publicly.
    """

    def __init__(self, _url, _request_method, _request_kwargs, _props):
        super().__init__()
        self.properties = _props
        self._method = _request_method
        self._kwargs = _request_kwargs
        self._rsp = None
        self._url = _url

    def _call(self):
        try:
            self._rsp = self._method(self._url, **self._kwargs)
        except (ConnectionError,) as e:
            raise exceptions.NetworkError(str(e))

    @property
    def response(self):
        "Underlying response object"
        return self._rsp

    @property
    def json(self):
        "Response json data"
        return self._rsp.json()

    @property
    def text(self):
        "Response text data"
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
    Make a HTTP request

    Args:
        url: url
        properties: a :class:`.RequestProperties` object

    Returns:
        a :class:`.Response` object
    """

    def __init__(self, url: str, properties: RequestProperties):
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

    Args:
        url: url
        properties: a :class:`.RequestProperties` object

    Returns:
        a :class:`.Response` object
    """

    def __init__(self, url: str, properties: RequestProperties=RequestProperties(), **kwargs):
        properties.method = Method.GET
        return super().__init__(url, properties, **kwargs)


class SimplePOSTRequest(SimpleRequest):
    """
    A convenience wrapper around SimpleRequest for POST requests

    Args:
        url: url
        properties: a :class:`.RequestProperties` object

    Returns:
        a :class:`.Response` object
    """

    def __init__(self, url: str, properties: RequestProperties=RequestProperties(), **kwargs):
        properties.method = Method.POST
        return super().__init__(url, properties, **kwargs)


class MultiRequest(_Request):
    """
    Make multiple HTTP requests

    Args:
        urls: a list of urls
        properties: a :class:`.RequestProperties` object

    Returns:
        a :class:`.Response` object
    """

    def __init__(self, urls: typing.Sequence[str], properties: RequestProperties):
        assert isinstance(properties, RequestProperties)
        assert isinstance(urls, (tuple, list, set, dict))
        super().__init__(properties.session)
        self.properties = properties
        raise NotImplementedError


class MultiGETRequest(MultiRequest):
    """
    A convenience wrapper around MultiRequest for GET requests

    Args:
        urls: a list of urls
        properties: a :class:`.RequestProperties` object

    Returns:
        a :class:`.Response` object
    """

    def __init__(self, urls, properties: RequestProperties=RequestProperties(), **kwargs):
        properties.method = Method.GET
        return super().__init__(urls, properties, **kwargs)


class MultiPOSTRequest(MultiRequest):
    """
    A convenience wrapper around MultiRequest for POST requests

    Args:
        urls: a list of urls
        properties: a :class:`.RequestProperties` object

    Returns:
        a :class:`.Response` object
    """

    def __init__(self, urls, properties: RequestProperties=RequestProperties(), **kwargs):
        properties.method = Method.POST
        return super().__init__(urls, properties, **kwargs)
