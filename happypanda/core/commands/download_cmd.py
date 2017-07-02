from happypanda.common import utils, hlogger
from happypanda.core.command import Command, CommandEvent, CommandEntry
from happypanda.core.services import DownloadItem, DownloadService

log = hlogger.Logger(__name__)

class MultipleDownload(Command):
    """
    Download multiple items
    """
    pass

class SingleDownload(Command):
    """
    Download a single item
    """
    pass