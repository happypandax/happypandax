import attr
import requests
import cachecontrol
import os

from happypanda.common import (hlogger, exceptions, utils, constants, exceptions, config)
from happypanda.core.command import CoreCommand, CommandEntry, Command
from happypanda.core.commands import io_cmd
from happypanda.core.services import NetworkService
from happypanda.interface import enums

log = hlogger.Logger(__name__)

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
    name = attr.ib(default="") # for logging
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

class Response(CoreCommand):
    """
    """

    def __init__(self, _response_obj, _props):
        super().__init__()
        self.properties = _props
        self._rsp = _response_obj

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
        if isinstance(str):
            filepath = io_cmd.CoreFS(filepath)

        if extension:
            filepath = io_cmd.CoreFS(filepath.path+os.path.splitext(self._rsp.url)[1], filepath._archive)

        with filepath.open(mode="wb") as f:
            if self.properties.stream:
                for data in self._rsp.iter_content(chunk_size=1024, decode_unicode=decode_unicode):
                    f.write(data)
                    f.flush()
            else:
                raise NotImplementedError
        return filepath.path

class _Request(Command):
    """
    """
    default_session = None
    
    def __init__(self, session=True, priority = constants.Priority.Low):
        super().__init__(priority)
        if not _Request.default_session:
            with utils.intertnal_db() as db:
                _Request.default_session = db.get("network_session", cachecontrol.CacheControl(requests.Session()))
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
        verb = Method.get(props.method) # TODO: wrap exceptions raised by APIEnum
        method = {
            'get':self.session.get,
            'post':self.session.post,
            'delete':self.session.delete,
            'put':self.session.put,
            'head':self.session.head,
            'options':self.session.options,
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
        r = Response(method(url, **kwargs), props)
        return r

    def cleanup_session(self):
        with utils.intertnal_db() as db:
            db['network_session'] = self.default_session



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

    def __init__(self, url, properties = RequestProperties(), **kwargs):
        properties.method = Method.GET
        return super().__init__(url, properties, **kwargs)

class SimplePOSTRequest(SimpleRequest):
    """
    A convenience wrapper around SimpleRequest for POST requests 
    """

    def __init__(self, url, properties = RequestProperties(), **kwargs):
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

    def __init__(self, url, properties = RequestProperties(), **kwargs):
        properties.method = Method.GET
        return super().__init__(url, properties, **kwargs)

class MultiPOSTRequest(MultiRequest):
    """
    A convenience wrapper around MultiRequest for POST requests 
    """

    def __init__(self, url, properties = RequestProperties(), **kwargs):
        properties.method = Method.POST
        return super().__init__(url, properties, **kwargs)