"""
"""
from gevent import monkey
monkey.patch_all() # necessary to make these functions play nice with gevent
import code
import sys

from happypanda.server.core import db
from happypanda.common import constants, message


## CORE ##
def interactive():
    ""
    code.interact(banner="======== Start Happypanda Interactive ========", local=globals())

## DATABASE ##



## GALLERY ##
def fetch_gallery(offset=None, from_gallery_id=None):
    """
    Fetch galleries from the database.
    Params:
        offset -- where to start fetching from, an int
        from_gallery -- which gallery id(index) to start fetching from, an int
    Returns:
        list of gallery message objects
    """
    pass

def add_gallery(galleries=[], paths=[]):
    """
    Add galleries to the database.
    Params:
        galleries -- list of gallery objects parsed from XML
        Returns: Status

        paths -- list of paths to the galleries
    Returns:
        Gallery objects
    """
    pass

def scan_gallery(paths=[], add_after=False, ignore_exist=True):
    """
    Scan folders for galleries
    Params:
        paths -- list of paths to folders to scan for galleries
        add_after -- add found galleries after scan
        ignore_exist -- ignore existing galleries
    Returns:
        list of paths to the galleries
    """
    pass


