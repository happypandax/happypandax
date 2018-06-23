"""
Events
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from happypanda.core import db, message
from happypanda.core.commands import database_cmd


def gallery_read_event(item_id: int=0):
    """
    An event for when a gallery is being read

    Args:
        item_id: id of gallery item

    Returns:
        bool indicating whether the event was succesful
    """
    s = False
    if item_id:
        sess = database_cmd.GetSession().run()
        g = sess.query(db.Gallery).filter(db.Gallery.id == item_id).one_or_none()
        if g:
            g.read()
            sess.commit()
            s = True
    return message.Identity('status', s)
