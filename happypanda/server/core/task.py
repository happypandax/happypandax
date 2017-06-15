from gevent import pool

from happypanda.common import constants, hlogger

log = hlogger.Logger(__name__)


class TaskRunner:
    ""

    def __init__(self, amount_of_tasks=constants.allowed_tasks):
        self._pool = pool.Pool(amount_of_tasks)
        self._commands = {}
        self._command_id = 0

    def run(self, command, *args, **kwargs):
        "Run a command async, returns id"

        self._command_id += 1
        task_id = self._command_id
        self._commands[task_id] = self._pool.spawn(
            command.run, *args, **kwargs)
        return task_id

    def command_done(self, command_id):
        ""
        if command_id in self._commands:
            return self._commands[command_id].ready()
        return True

    def get_value(self, command_id):
        ""
        if self.command_done(command_id):
            return self._commands[command_id].value()
