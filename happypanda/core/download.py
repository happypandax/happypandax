import enum

from happypanda.common import utils, hlogger
from happypanda.core import plugins, command

log = hlogger.Logger(__name__)

class DownloadState(enum.Enum):
    in_queue = 0
    downloading = 1
    finished = 2
    cancelled = 4

class DownloadItem(command.AsyncCommand):

    def __init__(self, service, url, session=None):
        assert isinstance(service, DownloadService)
        super().__init__(service)
        self.session = session
        self.url = url
        self.file = ""
        self.name = ""
        

    def main(self):
        return super().main(*args, **kwargs)

class DownloadService(command.Service):
    "A download service"

    def __init__(self):
        super().__init__("download")







