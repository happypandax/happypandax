from collections import UserList

from happypanda.common import constants, hlogger, utils

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


class Invalidator:
    """
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


class CacheInvalidation:
    similar_gallery = Invalidator()


constants.invalidator = CacheInvalidation()


class InternalDatabase:

    class GetSet:

        def __init__(self, key):
            self.key = key

        def get(self, default=None):
            with utils.intertnal_db() as db:
                return db.get(self.key, default)

        def set(self, value):
            with utils.intertnal_db() as db:
                db[self.key] = value

        def __call__(self, default=None):
            return self.get(default)

    latest_release = GetSet("latest_release")
    update_info = GetSet(constants.updater_key)
    network_session = GetSet("network_session")

    similar_gallery_calc = GetSet("similar_gallery_calc")
    similar_gallery_tags = GetSet("similar_gallery_tags")

    plugins_state = GetSet("plugins_state")


constants.internaldb = internaldb = InternalDatabase()
