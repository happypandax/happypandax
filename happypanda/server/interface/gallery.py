from happypanda.common import constants, message
from happypanda.server.core import db

def gallery_view(ctx=None, page=0, limit=100, search_filter="", list_id=None, gallery_filter=constants.GalleryFilter.Library):
    """
    Fetch galleries from the database.
    Provides pagination.

    Params:
        - page -- current page
        - limit -- amount of galleries per page
        - search_filter -- filter gallery by search terms
        - list_id -- current gallery list id
        - gallery_filter -- ...

    Returns:
        list of gallery message objects
    """

    s = constants.db_session()
    q = s.query(db.Gallery).limit(limit)
    glist = message.List("gallery", message.Gallery)
    [glist.append(message.Gallery(x)) for x in q.all()]
    return glist

def add_gallery(ctx=None, galleries=[], paths=[]):
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

def scan_gallery(ctx=None, paths=[], add_after=False, ignore_exist=True):
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


