from gevent import pool

from happypanda.common import constants, utils

log = utils.Logger(__name__)


class TaskRunner:
    ""

    def __init__(self, amount_of_tasks=constants.allowed_tasks):
        self._pool = pool.Pool(amount_of_tasks)
        self._tasks = {}
        self._task_id = 0

    def run(self, func, *args, **kwargs):
        "Run a task, returns id"
        self._task_id += 1
        task_id = self._task_id
        self._tasks[task_id] = self._pool.spawn(func, *args, **kwargs)
        return task_id

    def task_done(self, task_id):
        ""
        if task_id in self._tasks:
            return self._tasks[task_id].ready()
        return True

    def get_value(self, task_id):
        ""
        if self.task_done(task_id):
            return self._tasks[task_id].value()
