from happypanda.common import hlogger
from happypanda.core.command import Command

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
