from happypanda.common import utils, hlogger
from happypanda.core.command import Command, CommandEvent, CommandEntry
from happypanda.core.download import CommandItem, DownloadService

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