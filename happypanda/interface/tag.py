"""
Tags
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""

from happypanda.core import db, message
from happypanda.interface import enums
from happypanda.core.commands import database_cmd


def get_tags(item_type: enums.ItemType = enums.ItemType.Gallery,
             item_id: int = 0,
             raw: bool = False):
    """
    Get tags for item

    Args:
        item_type: possible items are :attr:`.ItemType.Gallery`, :attr:`.ItemType.Page`,
            :attr:`.ItemType.Grouping`, :attr:`.ItemType.Collection`
        item_id: id of item to fetch tags for
        raw: if true, tags from descendant ItemType's will not be included
            (this only makes sense when ItemType is :attr:`.ItemType.Gallery`)

    Returns:
        .. code-block:: guess

            {
                namespace : [ tag message object, ...],
                ...
            }
    """

    item_type = enums.ItemType.get(item_type)

    _, db_item = item_type._msg_and_model(
        (enums.ItemType.Gallery, enums.ItemType.Collection, enums.ItemType.Grouping, enums.ItemType.Page))

    db_obj = database_cmd.GetModelItemByID().run(db_item, {item_id})
    if db_obj:
        db_obj = db_obj[0]

    nstags = []
    if db_obj:
        g_objs = []
        if issubclass(db_item, db.TaggableMixin):
            nstags = db_obj.tags.all()
            if not raw and isinstance(db_obj, db.Gallery):
                g_objs.append(db_obj)
        else:
            for g in db_obj.galleries.all():
                nstags.extend(g.tags.all())
                if not raw:
                    g_objs.append(g)

        for g_obj in g_objs:
            for p in g_obj.pages.all():  # TODO: we only need tags
                nstags.extend(p.tags.all())

    msg = {}
    _msg = {}
    for nstag in nstags:
        ns = nstag.namespace.name
        if ns not in msg:
            msg[ns] = []
            _msg[ns] = []

        if nstag.tag.name not in _msg[ns]:
            msg[ns].append(message.Tag(nstag.tag, nstag).json_friendly(include_key=False))
            _msg[ns].append(nstag.tag.name)

    return message.Identity('tags', msg)
