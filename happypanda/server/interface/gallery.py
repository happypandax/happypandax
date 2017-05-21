from happypanda.common import constants, message, exceptions, utils
from happypanda.server.core import db
from happypanda.server.interface import enums

def get_image(item_type=enums.ItemType.Gallery.name,
              item_ids=[],
              size=enums.ImageSize.Medium.name,
              local=False,
              ctx=None):
    """
    Get cover image

    Params:
        - item_type -- ...
        - item_ids -- list of item ids
        - size -- ...
        - local -- replace image content with local path to image file

    Returns:
        a dict of id:content
    """
    utils.require_context(ctx)

    item_type = enums.ItemType.get(item_type)
    size = enums.ImageSize.get(size)

    db_items = {
        enums.ItemType.Gallery : (db.Gallery, message.Gallery),
        enums.ItemType.Collection : (db.Collection, message.Collection),
        enums.ItemType.Grouping : (db.Grouping, message.DatabaseMessage),
        enums.ItemType.Page : (db.Page, message.Page),
        }

    db_item = db_items.get(item_type)

    content = {}

    s = constants.db_session()

    for i in item_ids:
        
        p_data, p_path = s.query(db.Profile.data, db.Profile.path).filter(
                db_item.profiles.any(
                    db.and_op(
                        db_item.id == i,
                        db.Profile.size == size.name
                        ))).one_or_none()
        if not p:
            raise NotImplementedError
        else:
            if local:
                content[i] = p_path
            else:
                content[i] = p_data

    return message.Identity("image", content)


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


