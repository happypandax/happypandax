import sys
import gevent
import weakref


class Greenlet(gevent.Greenlet):
    '''
    A subclass of gevent.Greenlet which adds additional members:
     - locals: a dict of variables that are local to the "spawn tree" of
       greenlets
     - spawner: a weak-reference back to the spawner of the
       greenlet
     - stacks: a record of the stack at which the greenlet was
       spawned, and ancestors
    '''

    def __init__(self, f, *a, **kw):
        super(Greenlet, self).__init__(f, *a, **kw)
        self._hp_inherit(weakref.proxy(gevent.getcurrent()), sys._getframe())

    def _hp_inherit(self, parent, frame):
        spawner = self.spawn_parent = parent
        if not hasattr(spawner, 'locals'):
            spawner.locals = {}
        self.locals = spawner.locals
        stack = []
        cur = frame
        while cur:
            stack.extend((cur.f_code, cur.f_lineno))
            cur = cur.f_back
        self.stacks = (tuple(stack),) + getattr(spawner, 'stacks', ())[:10]
