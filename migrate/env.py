from __future__ import with_statement
from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig
import logging
import os
import sys

sys.path.insert(0, os.getcwd())

from happypanda.common import constants, config as hpx_config # noqa: E402
from happypanda.core import db # noqa: E402

USE_TWOPHASE = False

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

if config.attributes.get('configure_logger', True):
    # Interpret the config file for Python logging.
    # This line sets up loggers basically.
    fileConfig(config.config_file_name)
logger = logging.getLogger(constants.log_ns_database + 'alembic.env')

# gather section names referring to different
# databases.  These are named "engine1", "engine2"
# in the sample .ini file.
db_names = config.get_main_option('databases')
# add your model's MetaData objects here
# for 'autogenerate' support.  These must be set
# up to hold just those tables targeting a
# particular database. table.tometadata() may be
# helpful here in case a "copy" of
# a MetaData is needed.
# from myapp import mymodel
# target_metadata = {
#       'engine1':mymodel.metadata1,
#       'engine2':mymodel.metadata2
# }
target_metadata = {'main': db.Base.metadata}

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

if context.get_x_argument(as_dictionary=True).get('dev', None):
    dev_db = True
else:
    dev_db = hpx_config.dev_db.value


def get_engines(offline=False):
    db_url = str(db.make_db_url(dev_db=dev_db))
    engines = {}
    if offline:
        engines = {'main': {'url': db_url}}
    else:
        engines = {'main': {'engine': engine_from_config(
            {'here': os.getcwd(), 'sqlalchemy.url': db_url},
            prefix='sqlalchemy.',
            poolclass=pool.NullPool)}}
    return engines


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # for the --sql use case, run migrations for each URL into
    # individual files.

    engines = get_engines(True)

    for name, rec in engines.items():
        logger.info("Migrating database %s" % name)
        file_ = "%s.sql" % name
        logger.info("Writing output to %s" % file_)
        with open(file_, 'w') as buffer:
            context.configure(url=rec['url'], output_buffer=buffer,
                              target_metadata=target_metadata.get(name),
                              literal_binds=True)
            with context.begin_transaction():
                context.run_migrations(engine_name=name)


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    # for the direct-to-DB use case, start a transaction on all
    # engines, then run all migrations, then commit all transactions.

    engines = get_engines()

    for name, rec in engines.items():
        engine = rec['engine']
        rec['connection'] = conn = engine.connect()

        if USE_TWOPHASE:
            rec['transaction'] = conn.begin_twophase()
        else:
            rec['transaction'] = conn.begin()

    def process_revision_directives(context, revision, directives):
        if config.cmd_opts.autogenerate:
            script = directives[0]
            if script.upgrade_ops.is_empty():
                logger.info("No changes detected.")
                directives[:] = []

    try:
        for name, rec in engines.items():
            logger.info("Migrating database %s" % name)
            context.configure(
                connection=rec['connection'],
                upgrade_token="%s_upgrades" % name,
                downgrade_token="%s_downgrades" % name,
                target_metadata=target_metadata.get(name),
                process_revision_directives=process_revision_directives
            )
            context.run_migrations(engine_name=name)

        if USE_TWOPHASE:
            for rec in engines.values():
                rec['transaction'].prepare()

        for rec in engines.values():
            rec['transaction'].commit()
    except BaseException:
        for rec in engines.values():
            rec['transaction'].rollback()
        raise
    finally:
        for rec in engines.values():
            rec['connection'].close()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
