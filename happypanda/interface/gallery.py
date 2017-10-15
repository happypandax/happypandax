"""
Gallery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

from happypanda.common import exceptions, utils
from happypanda.core.commands import database_cmd
from happypanda.core import message, db


def add_gallery(galleries: list=[], paths: list=[]):
    """
    Add galleries to the database.

    Args:
        galleries: list of gallery objects
        paths: list of paths to the galleries

    Returns:
        Gallery objects
    """
    return message.Message("works")


def scan_gallery(paths: list=[], add_after: bool=False,
                 ignore_exist: bool=True):
    """
    Scan folders for galleries

    Args:
        paths: list of paths to folders to scan for galleries
        add_after: add found galleries after scan
        ignore_exist: ignore existing galleries

    Returns:
        list of paths to the galleries
    """
    return message.Message("works")


def get_page(page_id: int=None, gallery_id: int=None, number: int=0, prev: bool=False):
    """
    Get next/prev page by either gallery or page id

    Args:
        page_id: id of page
        gallery_id: id of gallery
        number: retrieve specific page number
        prev: by default next page is retrieved, to retrieve prev page set this to true

    Returns:
        Page object
    """
    if not (gallery_id or page_id):
        raise exceptions.APIError(
                utils.this_function(),
                "Either a gallery id or page id is required")

    item = None

    if page_id:
        p = database_cmd.GetModelItemByID().run(db.Page, {page_id})[0]
        if number and p and number == p.number:
            item = p
        elif p:
            number = number or p.number
            gallery_id = p.gallery_id

    if not item:
        f = db.Page.number < number if prev else db.Page.number > number
        f = db.and_op(f, db.Page.gallery_id==gallery_id)
        item = database_cmd.GetModelItemByID().run(db.Page,
                                                    order_by=db.Page.number.desc() if prev else db.Page.number,
                                                    filter=f,
                                                    limit=1)
        if item:
            item = item[0]

    return message.Page(item) if item else None