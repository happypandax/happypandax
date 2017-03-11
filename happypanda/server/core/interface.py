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
    "test"
    code.interact(banner="======== Start Happypanda Interactive ========", local=globals())

## DATABASE ##



## GALLERY ##
def fetch_galleries(gallery_ids=[]):
    """
    Fetch galleries from the database.

    Params:
        - gallery_ids -- list of gallery id whose corresponding gallery is to be fetched

    Returns:
        list of gallery message objects
    """
    return message.Message("works")

def gallery_view(page=0, gallery_limit=100, search_filter="", list_id=0, gallery_filter=constants.GalleryFilter):
    """
    Fetch galleries from the database.
    Provides pagination.

    Params:
        - page -- current page
        - gallery_limit -- amount of galleries per page
        - search_filter -- filter gallery by search terms
        - list_id -- current gallery list id
        - gallery_filter -- ...

    Returns:
        list of gallery message objects
    """

    return message.Message("works")

def add_gallery(galleries=[], paths=[]):
    """
    Add galleries to the database.

    Params:
        - galleries -- list of gallery objects parsed from XML

            Returns:
                Status

        - paths -- list of paths to the galleries

    Returns:
        Gallery objects
    """
    return message.Message("works")

def scan_gallery(paths=[], add_after=False, ignore_exist=True):
    """
    Scan folders for galleries

    Params:
        - paths -- list of paths to folders to scan for galleries
        - add_after -- add found galleries after scan
        - ignore_exist -- ignore existing galleries

    Returns:
        list of paths to the galleries
    """
    return message.Message("works")


## 
def set_settings(namespace, set_dict={}):
    """
    Set settings

    Params:
        - set_dict -- a dictionary containing key:value pairs :D

    Returns:
        Status
    """
    return message.Message("works")

def get_settings(namespace, set_list=[]):
    """
    Set settings
    Use setting key 'all' to fetch all setting key:values

    Params:
        - set_list -- a list of setting keys

    Returns:
        dict of setting_key:value
    """
    return message.Message("works")
