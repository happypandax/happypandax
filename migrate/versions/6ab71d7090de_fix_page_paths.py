"""fix page paths

Revision ID: 6ab71d7090de
Revises: 
Create Date: 2018-07-15 15:20:24.502077

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Text, Integer, bindparam
from sqlalchemy.sql import table, column, select
import pathlib


# revision identifiers, used by Alembic.
revision = '6ab71d7090de'
down_revision = None
branch_labels = None
depends_on = None


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()


page = table("page",
    column('id', Integer),
    column('path', Text),
    )


def upgrade_main():
    conn = op.get_bind()
    pages = conn.execute(select([page.c.id, page.c.path]))
    new_page_paths = []
    for page_id, page_path in pages:
        new_page_paths.append({'page_id': page_id, 'new_path':str(pathlib.Path(page_path))})
    if new_page_paths:
        stmt = page.update().\
                    where(page.c.id==bindparam('page_id')).\
                    values(path=bindparam('new_path'))
        conn.execute(stmt, new_page_paths)


def downgrade_main():
    pass

