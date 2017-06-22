from happypanda.common import utils, hlogger, exceptions
from happypanda.server.core.command import Command, CommandEvent, CommandEntry
from happypanda.server.core import db

log = hlogger.Logger(__name__)

class GetModel(Command):
    """
    Returns a database model by name
    """

    def __init__(self):
        super().__init__()

    def main(self, model_name:str) -> db.Base:
        
        if not hasattr(db, model_name):
            raise exceptions.CoreError(utils.this_command(self), "No database model named '{}'".format(model_name))

        return getattr(db, model_name)

class Session(Command):
    """
    A database session
    """

    def __init__(self):
        super().__init__()

    def main(self, *args, **kwargs):
        return super().main(*args, **kwargs)
