from happypanda.common import constants, message
from happypanda.server.core import db

def get_profile(ctx=None, item_type=constants.ItemType.Gallery, item_ids=[], size=None, local=False):
    """
    Get cover image

    Params:
        - item_type -- ...
        - item_ids -- list of item ids
        - size -- string specifying image size, e.g.: '200x200'. Leave none for default size.
        - local -- replace image content with local path to image file

    Returns:
        list of paths to the galleries
    """
    return message.Message("works")