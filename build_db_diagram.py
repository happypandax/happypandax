import sadisplay
from happypanda.core import db


def exclude(attr):
    ""
    if attr.endswith('_profiles'):
        return True

    if 'life' == attr.lower():
        return True

    if 'event' == attr.lower():
        return True

    if 'user' == attr.lower():
        return True


attrs = [getattr(db, attr) for attr in dir(db) if not exclude(attr)]

desc = sadisplay.describe(
    attrs,
    show_methods=False,
    show_properties=True,
    show_indexes=False,
    show_simple_indexes=False,
    show_columns_of_indexes=False
)

with open('schema.dot', 'w', encoding='utf-8') as f:
    f.write(sadisplay.dot(desc))
