import pdb
import sys
import os
import tinydb
import __main__

from tinydb.storages import MemoryStorage
from collections import UserList
from dogpile.cache.region import make_region
from dogpile.cache.util import kwarg_function_key_generator

from happypanda.common import constants, hlogger

log = hlogger.Logger(constants.log_ns_misc + __name__)


class AttributeList(UserList):
    """
    l = AttributeList("one", "two")
    l.one == "one"
    l.two == "two"

    """

    def __init__(self, *names):
        self._names = {str(x): x for x in names}
        super().__init__(names)

    def __getattr__(self, key):
        if key in self._names:
            return self._names[key]
        raise AttributeError("AttributeError: no attribute named '{}'".format(key))


class AttributeDict(dict):
    """
    l = AttributeDict()
    l.one = "yes"
    l['one'] == 'yes'
    l.one == "yes"
    'one' in l
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __setattr__(self, name, value):
        self[name] = value

    def __getattr__(self, key):
        if key in self:
            return self[key]
        raise AttributeError("AttributeError: no attribute named '{}'".format(key))


constants.cache_regions = AttributeDict()
constants.cache_regions['db'] = make_region(
    name='db',
    function_key_generator=kwarg_function_key_generator,
).configure(
    'dogpile.cache.memory', # !! remember to add to pyinstaller hidden import
    expiration_time=60 * 60  # 1 hour
)


class Invalidator:
    """
    An invalidation implementation.
    Acts like a switch that turns to false on subsequent access
    """

    def __init__(self, parent=None, value=False):
        assert parent is None or isinstance(parent, Invalidator)
        self.parent = parent
        self.children = []
        self.value = value
        if self.parent:
            self.parent.children.append(self)
            self.value = self.parent.value

    def __get__(self, instance, objtype):
        v = self.value
        if self.value:
            self.value = False
        return v

    def __set__(self, instance, value):
        self._set(value)

    def _set(self, value):
        self.value = value
        for c in self.children:
            c._set(value)


class BaseInvalidation:

    @classmethod
    def set(cls, name, value):
        cls.__dict__[name]._set(value)

    @classmethod
    def get(cls, name):
        return getattr(cls, name)


class CacheInvalidation(BaseInvalidation):
    dirty_tags = Invalidator()
    similar_gallery = Invalidator(dirty_tags)
    dirty_database = Invalidator(dirty_tags)


constants.invalidator = CacheInvalidation()


class _Nothing:
    pass


class InternalTinyDB:

    query = tinydb.Query()

    class GetSet:

        def __init__(self, idb, key, default=None):
            self._idb = idb
            self.key = key
            if default is not None:
                self.set(default)

        def get(self, default=_Nothing):
            return self._idb.get(self.key, default)

        def set(self, value):
            return self._idb.set(self.key, value)

        def __call__(self, default=_Nothing):
            return self.get(default)

    def __init__(self, db):
        self._db = db

    def get(self, key, default=_Nothing):
        r = self._db.get(self.query.key == key)
        if r is None:
            if default == _Nothing:
                raise KeyError(f"Key {key} does not exist")
            return default
        v = r['value']
        if r['type'] == str(type(tuple)):
            v = tuple(v)
        return v

    def set(self, key, value):
        self._db.upsert({'key': key, 'value': value, 'type': str(type(value))}, self.query.key == key)

    def __contains__(self, k):
        return self._db.contains(self.query.key == k)

    def __getitem__(self, key):
        return self.get(key)

    def __setitem__(self, key, value):
        self.set(key, value)

    def __delitem__(self, key):
        raise NotImplementedError

    def __iter__(self):
        raise NotImplementedError

    def __len__(self):
        return len(self._db)


class InternalDatabase(InternalTinyDB):

    def __init__(self, db_path):
        os.makedirs(os.path.split(db_path)[0], exist_ok=True)
        super().__init__(tinydb.TinyDB(db_path))

        self.release_tags = self.GetSet(self, "release_tags")
        self.latest_release = self.GetSet(self, "latest_release")
        self.update_info = self.GetSet(self, constants.updater_key)
        self.network_session = self.GetSet(self, "network_session")

        self.similar_gallery_calc = self.GetSet(self, "similar_gallery_calc")
        self.similar_gallery_tags = self.GetSet(self, "similar_gallery_tags")

        self.plugins_state = self.GetSet(self, "plugins_state")

        self.scheduler_commands = self.GetSet(self, "scheduler_commands")


class InternalStore(InternalTinyDB):

    def __init__(self):
        super().__init__(tinydb.TinyDB(storage=MemoryStorage))
        self.temp_view = InternalTinyDB(self._db.table("temp_view"))
        self.galleryfs_addition = self.GetSet(self.temp_view, "galleryfs_addition", {})


constants.store = store = InternalStore()

in_test = hasattr(sys, "_called_from_test")
if in_test:
    constants.internaldb = internaldb = None
else:
    constants.internaldb = internaldb = InternalDatabase(constants.internal_db_path)

in_repl = not hasattr(__main__, '__file__') or in_test
if getattr(sys, 'frozen', False):
    in_repl = True


class ForkablePdb(pdb.Pdb):

    if not in_repl:
        _original_stdin_fd = sys.stdin.fileno()
        _original_stdin = None

    def __init__(self):
        pdb.Pdb.__init__(self, nosigint=True)

    def _cmdloop(self):
        current_stdin = sys.stdin
        try:
            if not self._original_stdin:
                self._original_stdin = os.fdopen(self._original_stdin_fd)
            sys.stdin = self._original_stdin
            self.cmdloop()
        finally:
            sys.stdin = current_stdin


if not in_repl and __name__ == '__mp_main__' or (__name__ == '__main__' and len(
        sys.argv) >= 2 and sys.argv[1] == '--multiprocessing-fork'):
    pdb.set_trace = ForkablePdb().set_trace
