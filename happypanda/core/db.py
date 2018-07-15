import sys
import arrow
import os
import enum
import re
import bcrypt
import warnings
import functools
import gevent
import threading
import pathlib
import langcodes
import inspect as pyinspect
import alembic.config
import alembic.command
import alembic.script
import alembic.migration
import datetime

from contextlib import contextmanager
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL, make_url as sa_make_url
from sqlalchemy import String as _String
from sqlalchemy import Text as _Text
from sqlalchemy import exc as sa_exc
from sqlalchemy.inspection import inspect
from sqlalchemy.ext.mutable import Mutable
from sqlalchemy.ext.declarative import declared_attr, as_declarative
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.ext.indexable import index_property
from sqlalchemy.ext.hybrid import hybrid_property, hybrid_method
from sqlalchemy.ext.associationproxy import AssociationProxy
from sqlalchemy.sql.expression import BinaryExpression, func, literal
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql.operators import custom_op
from sqlalchemy.ext import orderinglist
from sqlalchemy.orm import (
    sessionmaker,
    relationship,
    validates,
    object_session,
    scoped_session,
    attributes,
    properties,
    state,
    collections,
    dynamic,
    backref,
    exc as exc_orm,
)
from sqlalchemy import (
    create_engine,
    event,
    exc,
    desc,
    and_,
    or_,
    Boolean,
    Column,
    Integer,
    ForeignKey,
    Table,
    UniqueConstraint,
    PrimaryKeyConstraint,
    Enum,
    TypeDecorator,
    text,
    select)
from sqlalchemy_utils import (
    ArrowType,
    generic_repr,
    force_instant_defaults,
    force_auto_coercion,
    get_type,
    JSONType as JSONType_)
from sqlalchemy_utils.functions import create_database, database_exists

from happypanda.common import constants, exceptions, hlogger, clsutils, config, utils

force_instant_defaults()
force_auto_coercion()

log = hlogger.Logger(constants.log_ns_database + __name__)

and_op = and_
or_op = or_
sa_text = text
desc_expr = desc

expunge_cascade = "save-update, merge, refresh-expire, expunge"
default_cascade = "save-update, merge, refresh-expire"


class OrderingQuery(dynamic.AppenderQuery):
    """
    Mixes OrderedList and AppenderQuery
    """

    def __init__(self, attr, state):
        super().__init__(attr, state)
        self.ordering_attr = "number"
        self.ordering_func = orderinglist.count_from_1
        self.reorder_on_append = False
        self._len = None

    # More complex serialization schemes (multi column, e.g.) are possible by
    # subclassing and reimplementing these two methods.
    def _get_order_value(self, entity):
        return getattr(entity, self.ordering_attr)

    def _set_order_value(self, entity, value):
        setattr(entity, self.ordering_attr, value)

    def reorder(self, _iterable=None):
        """Synchronize ordering for the entire collection.
        Sweeps through the list and ensures that each object has accurate
        ordering information set.
        """
        for index, entity in enumerate(_iterable or self):
            self._order_entity(index, entity, True)

    # As of 0.5, _reorder is no longer semi-private
    _reorder = reorder

    def _order_entity(self, index, entity, reorder=True):
        have = self._get_order_value(entity)

        # Don't disturb existing ordering if reorder is False
        if have is not None and not reorder:
            return

        should_be = self.ordering_func(index, self)
        if have != should_be:
            self._set_order_value(entity, should_be)

    def __len__(self):
        if self._len is None:
            self._len = self.count()
        return self._len

    def append(self, entity, enable_count_cache=False):
        super().append(entity)
        if not enable_count_cache:
            self._len = None
        else:
            self._len = 0 if self._len is None else self._len
            self._len + 1
        self._order_entity(len(self) - 1, entity, self.reorder_on_append)

    def insert(self, index, entity, enable_count_cache=False):
        items = list(self)
        s = object_session(entity)
        if inspect(entity).deleted or s and entity in s.deleted:
            # see warning
            # http://docs.sqlalchemy.org/en/latest/orm/extensions/orderinglist.html?highlight=orderinglist#module-sqlalchemy.ext.orderinglist
            raise exceptions.DatabaseError(utils.this_function(),
                                           "Two entries trading values is not supported")
        else:
            items.insert(index, entity)

        super().append(entity)
        if not enable_count_cache:
            self._len = None
        else:
            self._len = 0 if self._len is None else self._len
            self._len + 1
        self._reorder(items)

    def extend(self, iterator, enable_count_cache=False):
        for i in iterator:
            self.append(i, enable_count_cache=enable_count_cache)

    def remove(self, entity, enable_count_cache=False):
        super().remove(entity)
        if not enable_count_cache:
            self._len = None
        else:
            self._len = 0 if self._len is None else self._len
            self._len -= 1
        self._reorder()

    def pop(self, index=-1, enable_count_cache=False):
        entity = super().pop(index)
        if not enable_count_cache:
            self._len = None
        else:
            self._len = 0 if self._len is None else self._len
            self._len -= 1
        self._reorder()
        return entity

    def __setitem__(self, index, entity):
        self._len = None
        if isinstance(index, slice):
            step = index.step or 1
            start = index.start or 0
            count = len(self)
            if start < 0:
                start += count
            stop = index.stop or count
            if stop < 0:
                stop += count

            for i in range(start, stop, step):
                self.__setitem__(i, entity[i])
        else:
            self._order_entity(index, entity, True)
            super().__setitem__(index, entity)

    def __delitem__(self, index):
        self._len = None
        super().__delitem__(index)
        self._reorder()

    def __setslice__(self, start, end, values):
        self._len = None
        super().__setslice__(start, end, values)
        self._reorder()

    def __delslice__(self, start, end):
        self._len = None
        super().__delslice__(start, end)
        self._reorder()

    def __reduce__(self):
        return orderinglist._reconstitute, (self.__class__, self.__dict__, list(self))


class JSONType(JSONType_):
    """
    Use JSONB instead of JSON
    """

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(JSONB())
        else:
            return dialect.type_descriptor(self.impl)


class Text(_Text):

    def __init__(self, length=65535 if config.dialect.value == constants.Dialect.MYSQL else None, *args, **kwargs):
        return super().__init__(length, *args, **kwargs)


class String(_String):
    """Enchanced version of standard SQLAlchemy's :class:`String`.
    Supports additional operators that can be used while constructing
    filter expressions.
    """

    def __init__(self, length=255, *args, **kwargs):
        return super().__init__(length, *args, **kwargs)

    class comparator_factory(_String.comparator_factory):
        """Contains implementation of :class:`String` operators
        related to regular expressions.
        """

        def regexp(self, other):
            return RegexMatchExpression(
                self.expr, literal(other), custom_op('~'))

        def iregexp(self, other):
            return RegexMatchExpression(
                self.expr, literal(other), custom_op('~*'))

        def not_regexp(self, other):
            return RegexMatchExpression(
                self.expr, literal(other), custom_op('!~'))

        def not_iregexp(self, other):
            return RegexMatchExpression(
                self.expr, literal(other), custom_op('!~*'))


class LowerCaseString(TypeDecorator):
    """
    Ensures strings a lowercased
    """
    impl = String

    def process_bind_param(self, value, dialect):
        return value.lower()


class CapitalizedString(TypeDecorator):
    """
    Ensures strings capitalized
    """
    impl = String

    def process_bind_param(self, value, dialect):
        return value.capitalize()


class RegexMatchExpression(BinaryExpression):
    """Represents matching of a column againsts a regular expression."""


SQLITE_REGEX_FUNCTIONS = {
    '~': ('REGEXP',
          lambda value, regex: bool(re.match(regex, value))),
    '~*': ('IREGEXP',
           lambda value, regex: bool(re.match(regex, value, re.IGNORECASE))),
    '!~': ('NOT_REGEXP',
           lambda value, regex: not re.match(regex, value)),
    '!~*': ('NOT_IREGEXP',
            lambda value, regex: not re.match(regex, value, re.IGNORECASE)),
}


class PasswordHash(Mutable):
    def __init__(self, hash_, rounds=None):
        assert len(hash_) == 60, 'bcrypt hash should be 60 chars.'
        assert hash_.count(b'$'), 'bcrypt hash should have 3x "$".'
        self.hash = hash_
        self.rounds = int(self.hash.split(b'$')[2])
        self.desired_rounds = rounds or self.rounds

    def __eq__(self, candidate):
        """Hashes the candidate string and compares it to the stored hash.

        If the current and desired number of rounds differ, the password is
        re-hashed with the desired number of rounds and updated with the results.
        This will also mark the object as having changed (and thus need updating).
        """
        if isinstance(candidate, str):
            if self.rounds < self.desired_rounds:
                self._rehash(candidate)
            if bcrypt.checkpw(self._encoded(candidate), self.hash):
                return True
        return False

    def __repr__(self):
        """Simple object representation."""
        return '<{}>'.format(type(self).__name__)

    @classmethod
    def coerce(cls, key, value):
        """Ensure that loaded values are PasswordHashes."""
        if isinstance(value, PasswordHash):
            return value
        return super(PasswordHash, cls).coerce(key, value)

    @classmethod
    def new(cls, password, rounds):
        """Returns a new PasswordHash object for the given password and rounds."""
        return cls(cls._new(password, rounds))

    @classmethod
    def _encoded(cls, txt):
        if isinstance(txt, str):
            txt = txt.encode('utf-8')
        return txt

    @staticmethod
    def _new(password, rounds):
        """Returns a new bcrypt hash for the given password and rounds."""
        return bcrypt.hashpw(PasswordHash._encoded(password), bcrypt.gensalt(rounds))

    def _rehash(self, password):
        """Recreates the internal hash and marks the object as changed."""
        self.hash = self._new(password, self.desired_rounds)
        self.rounds = self.desired_rounds
        self.changed()


class Password(TypeDecorator):
    """Allows storing and retrieving password hashes using PasswordHash."""
    impl = String

    def __init__(self, rounds=10, **kwds):
        self.rounds = rounds
        super().__init__(**kwds)

    def process_bind_param(self, value, dialect):
        """Ensure the value is a PasswordHash and then return its hash."""
        p = self._convert(value)
        return p.hash.decode('utf-8') if p else None

    def process_result_value(self, value, dialect):
        """Convert the hash to a PasswordHash, if it's non-NULL."""
        if value:
            value = PasswordHash._encoded(value)
            return PasswordHash(value, rounds=self.rounds)

    def validator(self, password):
        """Provides a validator/converter for @validates usage."""
        return self._convert(password)

    def _convert(self, value):
        """Returns a PasswordHash from the given string.

        PasswordHash instances or None values will return unchanged.
        Strings will be hashed and the resulting PasswordHash returned.
        Any other input will result in a TypeError.
        """
        if isinstance(value, PasswordHash):
            return value
        elif isinstance(value, (str, bytes)) and value:
            value = PasswordHash._encoded(value)
            return PasswordHash.new(value, self.rounds)
        elif value is not None:
            raise TypeError(
                'Cannot convert {} to a PasswordHash'.format(type(value)))


@as_declarative()
class Base:
    __table_args__ = {'mysql_collate': 'utf8mb4_unicode_ci'}

    id = Column(Integer, primary_key=True)
    _properties = Column(JSONType, nullable=False, default={})
    plugin = index_property('_properties', 'plugin', default={})

    def replace_with(self, obj):
        """
        """
        assert isinstance(obj, type(self))
        with no_autoflush(object_session(obj)):
            for k, v in obj.__dict__.items():
                setattr(self, k, v)

    def delete(self):
        sess = object_session(self)
        if not sess:
            sess = constants.db_session()
        with no_autoflush(sess):
            sess.delete(self)
        return sess

    def update(self, attr_name, value=None, op="add", **kw):
        """
        """
        ops = ("add", "remove")
        assert op in ops, f"op must be one of {ops}"

        if not isinstance(attr_name, str):
            attr_name = column_name(attr_name)

        if value is None and kw:
            value = kw

        col_model = column_model(getattr(self.__class__, attr_name))

        def do_op(x, v, o, check=True):
            if is_list(x) or is_query(x):
                if o == "add":
                    if check and v not in x:
                        x.append(v)
                    elif not check:
                        x.append(v)
                elif o == "remove":
                    if check and v in x:
                        x.remove(v)
                    elif not check:
                        x.remove(v)
                else:
                    raise NotImplementedError
            elif issubclass(col_model, Base):
                if o == "add":
                    setattr(self, attr_name, v)
                elif o == "remove":
                    setattr(self, attr_name, None)
            else:
                raise NotImplementedError

        with no_autoflush(object_session(self)):
            attr_value = getattr(self, attr_name)
            models = (NameMixin, )
            try:
                rel_col = issubclass(col_model, Base)
            except TypeError:
                rel_col = False

            if rel_col or is_list(attr_value) or is_query(attr_value):
                if not utils.is_collection(value) or isinstance(value, dict):
                    value = [value]

                for x in value:
                    if issubclass(col_model, MetaTag):
                        if isinstance(x, dict) and len(x.keys()) == 1 and 'name' in x:
                            x = x['name']

                        if isinstance(x, dict):  # {tag_name: True, tag_name:False, etc.}
                            for m_name, m_value in x.items():
                                mtag = col_model.as_unique(name=m_name)
                                if m_value:
                                    if mtag not in attr_value:
                                        attr_value.append(mtag)
                                else:
                                    if mtag in attr_value:
                                        attr_value.remove(mtag)
                        elif isinstance(x, list):
                            for m in x:
                                if isinstance(m, str):
                                    m = col_model.as_unique(name=m)
                                do_op(attr_value, m, op)
                        elif isinstance(x, str):
                            x = col_model.as_unique(name=x)
                            do_op(attr_value, x, op)
                        else:
                            do_op(attr_value, x, op)

                    elif isinstance(x, Base):
                        do_op(attr_value, x, op)
                    elif isinstance(x, str) and issubclass(col_model, models):
                        if issubclass(col_model, NameMixin):
                            v = col_model.as_unique(name=x)
                            do_op(attr_value, v, op)
                        else:
                            raise NotImplementedError
                    elif isinstance(x, dict) and rel_col:
                        if issubclass(col_model, UniqueMixin):
                            v = col_model.as_unique(**x)
                            do_op(attr_value, v, op)
                        else:
                            v = col_model(**x)
                            do_op(attr_value, v, op)
                    elif rel_col:
                        do_op(attr_value, x, op)
                    else:
                        do_op(attr_value, x, op)
            else:
                setattr(self, attr_name, value)


def _unique(session, cls, hashfunc, queryfunc, constructor, arg, kw):
    cache = getattr(session, '_unique_cache', None)
    if cache is None:
        session._unique_cache = cache = {}

    key = (cls, hashfunc(*arg, **kw))
    if key in cache:
        return cache[key]
    else:
        with session.no_autoflush:
            q = session.query(cls)
            q = queryfunc(q, *arg, **kw)
            obj = q.first()
            #import pdb; pdb.set_trace();
            if not obj:
                obj = constructor(*arg, **kw)
                session.add(obj)
        cache[key] = obj
        return obj


class UniqueMixin:
    @classmethod
    def unique_hash(cls, *arg, **kw):
        raise NotImplementedError()

    @classmethod
    def unique_filter(cls, query, *arg, **kw):
        raise NotImplementedError()

    @classmethod
    def as_unique(cls, *arg, session=None, **kw):
        return _unique(
            session or constants.db_session(),
            cls,
            cls.unique_hash,
            cls.unique_filter,
            cls,
            arg, kw
        )


class NameMixin(UniqueMixin):
    name = Column(String, nullable=False, default='', unique=True)

    def __init__(self, *args, name="", **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name

    @classmethod
    def unique_hash(cls, name):
        return name

    @classmethod
    def unique_filter(cls, query, name):
        return query.filter(cls.name == name)

    def exists(self, obj=False, strict=False, session=None):
        "obj: if true queries for the full object and returns it"
        if not session and not constants.db_session:
            return self
        sess = session or constants.db_session()
        if obj:
            if strict:
                e = sess.query(
                    self.__class__).filter_by(
                    name=self.name).scalar()
            else:
                e = sess.query(
                    self.__class__).filter(
                    self.__class__.name.ilike(
                        "%{}%".format(
                            self.name))).scalar()
            if not e:
                e = self
        else:
            if strict:
                e = sess.query(
                    self.__class__.id).filter_by(
                    name=self.name).scalar() is not None
            else:
                e = sess.query(
                    self.__class__.id).filter(
                    self.__class__.name.ilike(
                        "%{}%".format(
                            self.name))).scalar() is not None
        return e

    def __repr__(self):
        return "<{}(ID: {}, Name: {})>".format(
            self.__class__.__name__, self.id, self.name)


class LowerNameMixin(NameMixin):
    name = Column(LowerCaseString, nullable=False, default='', unique=True)

    @classmethod
    def as_unique(cls, *args, **kwargs):
        if 'name' in kwargs:
            kwargs['name'] = kwargs['name'].lower()
        return super().as_unique(*args, **kwargs)

    @classmethod
    def unique_hash(cls, *args, **kwargs):
        if 'name' in kwargs:
            kwargs['name'] = kwargs['name'].lower()
        return super().unique_hash(*args, **kwargs)

    @classmethod
    def unique_filter(cls, *args, **kwargs):
        if 'name' in kwargs:
            kwargs['name'] = kwargs['name'].lower()
        return super().unique_filter(*args, **kwargs)


class CapitalizedNameMixin(NameMixin):
    name = Column(CapitalizedString, nullable=False, default='', unique=True)

    @classmethod
    def as_unique(cls, *args, **kwargs):
        if 'name' in kwargs:
            kwargs['name'] = kwargs['name'].capitalize()
        return super().as_unique(*args, **kwargs)

    @classmethod
    def unique_hash(cls, *args, **kwargs):
        if 'name' in kwargs:
            kwargs['name'] = kwargs['name'].capitalize()
        return super().unique_hash(*args, **kwargs)

    @classmethod
    def unique_filter(cls, *args, **kwargs):
        if 'name' in kwargs:
            kwargs['name'] = kwargs['name'].capitalize()
        return super().unique_filter(*args, **kwargs)


class AliasMixin:

    @declared_attr
    def language_id(cls):
        return Column(Integer, ForeignKey('language.id'))

    @declared_attr
    def language(cls):
        return relationship("Language", cascade=expunge_cascade)

    @declared_attr
    def alias_for_id(cls):
        return Column(Integer, ForeignKey("{}.id".format(cls.__tablename__)), nullable=True)  # has one-child policy

    @declared_attr
    def alias_for(cls):
        return relationship(cls.__name__,
                            primaryjoin=('{}.c.id=={}.c.alias_for_id'.format(cls.__tablename__, cls.__tablename__)),
                            remote_side='{}.id'.format(cls.__name__),
                            backref=backref("aliases"))

    @validates('aliases')
    def validate_aliases(self, key, alias):
        # can't add to myself
        if alias == self:
            raise exceptions.DatabaseError(
                utils.this_function(),
                "Cannot make {} itself's alias".format(
                    self.__class__.__name__))
        return alias

    @validates('alias_for')
    def validate_alias_for(self, key, alias):
        if alias is None:
            warnings.warn(
                "{}.alias_for has been reset, remember to flush or commit session to avoid possible circulay dependency error".format(self.__class__.__name__))
        # point to the original nstag
        if alias and alias.alias_for:
            return alias.alias_for
        return alias

    def __init__(self, *args, **kwargs):
        return super().__init__(*args, **kwargs)


class ProfileMixin:

    def get_profile(self, profile_type):
        return ''


class UpdatedMixin:

    last_updated = Column(ArrowType, nullable=False, default=arrow.now)


class UserMixin:

    @declared_attr
    def user(cls):
        return relationship(
            "User",
            cascade=expunge_cascade)

    @declared_attr
    def user_id(cls):
        return Column(Integer, ForeignKey('user.id'), default=cls.current_user)

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.user = user

    @classmethod
    def current_user(cls):
        "Retrieve the current user"
        u = constants.default_user
        ctx = utils.get_context()
        if ctx:
            u = ctx.get('user')
        return u.id if u else None


def validate_int(value):
    if isinstance(value, str):
        try:
            value = int(value)
        except BaseException:
            raise AssertionError(
                "Column only accepts integer, not {}".format(
                    type(value)))
    else:
        assert isinstance(
            value, int) or value is None, "Column only accepts integer, not {}".format(
            type(value))
    return value


def validate_string(value):
    assert isinstance(
        value, str) or value is None, "Column only accepts string, not {}".format(
        type(value))
    return value


def validate_arrow(value):
    assert isinstance(
        value, (arrow.Arrow, datetime.datetime)) or value is None, "Column only accepts arrow or datetime types, not {}".format(
        type(value))
    return value


def validatejson(value):
    assert isinstance(
        value, dict) or value is None, "Column only accepts dict, not {}".format(
        type(value))
    return value


def validate_bool(value):
    assert isinstance(
        value, bool) or value is None, "Column only accepts boolean, not {}".format(
        type(value))
    return value


validators = {
    Integer: validate_int,
    String: validate_string,
    Text: validate_string,
    ArrowType: validate_arrow,
    Boolean: validate_bool,
    JSONType: validatejson,
}


@event.listens_for(Base, 'attribute_instrument')
def configure_listener(class_, key, inst):
    if not hasattr(inst.property, 'columns'):
        return

    @event.listens_for(inst, "set", retval=True)
    def set_(instance, value, oldvalue, initiator):
        validator = validators.get(inst.property.columns[0].type.__class__)
        if validator:
            return validator(value)
        else:
            return value


def profile_association(cls, bref="items"):
    if not issubclass(cls, Base):
        raise ValueError("Must be subbclass of Base")
    table_name = cls.__tablename__
    column = '{}_id'.format(table_name)
    assoc = Table(
        '{}_profiles'.format(table_name), Base.metadata, Column(
            'profile_id', Integer, ForeignKey('profile.id')), Column(
            column, Integer, ForeignKey(
                '{}.id'.format(table_name))), UniqueConstraint(
                    'profile_id', column))

    cls.profiles = relationship(
        "Profile",
        secondary=assoc,
        lazy='dynamic',
        backref=backref(bref, lazy="dynamic"),
        cascade="all")
    return assoc


def metatag_association(cls, bref="items"):
    if not issubclass(cls, Base):
        raise ValueError("Must be subbclass of Base")
    table_name = cls.__tablename__
    column = '{}_id'.format(table_name)
    assoc = Table(
        '{}_metatags'.format(table_name), Base.metadata, Column(
            'metatag_id', Integer, ForeignKey('metatag.id')), Column(
            column, Integer, ForeignKey(
                '{}.id'.format(table_name))), UniqueConstraint(
                    'metatag_id', column))

    cls.metatags = relationship(
        "MetaTag",
        secondary=assoc,
        lazy='joined',
        backref=backref(bref, lazy="dynamic"),
        cascade="all")

    def on_metatag_event(self, metatag, is_remove):
        """
        """
        if is_remove:
            pass
        else:
            if isinstance(self, Gallery) and metatag.name == MetaTag.names.favorite:
                if not self.rating and config.auto_rate_gallery_on_favorite.value:
                    self.rating = 10
        return metatag

    cls.on_metatag_event = on_metatag_event

    @event.listens_for(cls.metatags, 'remove', retval=True, propagate=True)
    def rec_remove(target, value, initator):
        return target.on_metatag_event(value, True)

    @event.listens_for(cls.metatags, 'append', retval=True, propagate=True)
    def rec_append(target, value, initator):
        return target.on_metatag_event(value, False)

    return assoc


def metalist_association(cls, bref="items"):
    if not issubclass(cls, Base):
        raise ValueError("Must be subbclass of Base")
    table_name = cls.__tablename__
    column = '{}_id'.format(table_name)
    assoc = Table(
        '{}_metalists'.format(table_name), Base.metadata, Column(
            'metalist_id', Integer, ForeignKey('metalist.id')), Column(
            column, Integer, ForeignKey(
                '{}.id'.format(table_name))), UniqueConstraint(
                    'metalist_id', column))

    cls.metalists = relationship(
        "MetaList",
        secondary=assoc,
        lazy='dynamic',
        backref=backref(bref, lazy="dynamic"),
        cascade="all")
    return assoc


def setup_preffered_name(cls):
    if not issubclass(cls, Base):
        raise ValueError("Must be subbclass of Base")

    def preferred_name(self):
        t = self.name_by_language(config.translation_locale.value)
        if not t and self.names:
            t = self.names[0]
        return t

    def name_by_language(self, language_code):
        language_code = utils.get_language_code(language_code)
        for n in self.names:
            if n.language and n.language.code == language_code:
                return n

    cls.name_by_language = hybrid_method(name_by_language)
    cls.preferred_name = hybrid_property(preferred_name)


def url_association(cls, bref="items"):
    if not issubclass(cls, Base):
        raise ValueError("Must be subbclass of Base")
    table_name = cls.__tablename__
    column = '{}_id'.format(table_name)
    assoc = Table(
        '{}_url'.format(table_name), Base.metadata, Column(
            'url_id', Integer, ForeignKey('url.id')), Column(
            column, Integer, ForeignKey(
                '{}.id'.format(table_name))), UniqueConstraint(
                    'url_id', column))

    cls.urls = relationship(
        "Url",
        secondary=assoc,
        lazy='joined',
        backref=backref(bref, lazy="dynamic"),
        cascade="all")
    return assoc


class Life(Base):
    __tablename__ = 'life'

    version = Column(String, nullable=False, default=constants.version_db_str)
    times_opened = Column(Integer, nullable=False, default=0)
    timestamp = Column(ArrowType, nullable=False, default=arrow.now)

    def __repr__(self):
        return "<Version: {}, times_opened:{}>".format(
            self.version, self.times_opened)


class MetaTag(NameMixin, Base):
    __tablename__ = 'metatag'

    names = clsutils.AttributeList("favorite",
                                   "inbox",
                                   "readlater",
                                   "trash",
                                   "follow",
                                   "read")
    tags = {}

    @classmethod
    def all_names(cls):
        sess = constants.db_session()
        return tuple(x[0] for x in sess.query(cls.name).all())


class User(NameMixin, Base):
    __tablename__ = 'user'

    class Role(enum.Enum):
        admin = 'admin'
        user = 'user'
        guest = 'guest'
        default = 'default'

    name = Column(String, nullable=False, default='')
    role = Column(Enum(Role), nullable=False, default=Role.guest)
    address = Column(String, nullable=False, default='')
    context_id = Column(String, nullable=False, default='')
    password = Column(Password)
    timestamp = Column(ArrowType, nullable=False, default=arrow.now)
    rights = Column(JSONType, nullable=False, default={})
    right_add_gallery = index_property("rights", "add_gallery", default=False)
    right_remove_gallery = index_property("rights", "remove_gallery", default=False)
    right_update_gallery = index_property("rights", "update_gallery", default=False)

    events = relationship("Event", lazy='dynamic', back_populates='user')

    @validates('password')
    def _validate_password(self, key, password):
        return getattr(type(self), key).type.validator(password)

    @property
    def has_auth(self):
        return self.role != self.Role.guest

    @property
    def is_admin(self):
        return self.role == self.Role.admin


metatag_association(User, "users")


@generic_repr
class Profile(Base):
    __tablename__ = 'profile'

    path = Column(Text, nullable=False, default='')
    data = Column(String, nullable=False, index=True)
    size = Column(String, nullable=False)
    timestamp = Column(ArrowType, nullable=False, default=arrow.now)
    custom = Column(Boolean, default=False)


class Event(Base):
    __tablename__ = 'event'

    class Action(enum.Enum):
        object_update = 'object_update'
        object_delete = 'object_delete'
        gallery_read = 'gallery_read'

    item_id = Column(Integer)
    name = Column(String, nullable=False, default="")
    by_table = Column(String, nullable=False, default="")
    timestamp = Column(ArrowType, nullable=False, default=arrow.now)
    action = Column(String, nullable=False)
    extra = Column(JSONType, nullable=False, default={})
    user_id = Column(Integer, ForeignKey('user.id'), default=UserMixin.current_user)
    user = relationship(
        "User",
        back_populates="events",
        cascade=expunge_cascade)

    def __init__(self, action, item, name=None, user_id=None, timestamp=None):
        assert isinstance(item, Base)
        if isinstance(action, Event.Action):
            action = action.value
        self.action = action
        self.user_id = user_id
        self.item_id = item.id
        self.by_table = item.__tablename__
        if name:
            self.name = name
        if timestamp:
            self.timestamp = timestamp


@generic_repr
class Hash(NameMixin, Base):
    __tablename__ = 'hash'


@generic_repr
class NamespaceTags(UniqueMixin, AliasMixin, UserMixin, Base):
    __tablename__ = 'namespace_tags'

    tag_id = Column(Integer, ForeignKey('tag.id'))
    namespace_id = Column(Integer, ForeignKey('namespace.id'))
    __table_args__ = (UniqueConstraint('tag_id', 'namespace_id'),)

    tag = relationship("Tag", cascade=expunge_cascade)
    namespace = relationship("Namespace",
                             cascade=expunge_cascade)

    parent_id = Column(Integer, ForeignKey("namespace_tags.id"), nullable=True)
    parent = relationship("NamespaceTags",
                          primaryjoin=('namespace_tags.c.id==namespace_tags.c.parent_id'),
                          remote_side='NamespaceTags.id',
                          backref=backref("children"))

    def __init__(self, ns=None, tag=None, **kwargs):
        super().__init__(**kwargs)
        if isinstance(ns, str):
            ns = Namespace.as_unique(name=ns)
        if isinstance(tag, str):
            tag = Tag.as_unique(name=tag)
        self.namespace = ns
        self.tag = tag
        if tag and not ns:
            self.namespace = Namespace.default()

    @validates('children')
    def validate_child(self, key, child):
        # can't add to myself
        if child == self:
            raise exceptions.DatabaseError(utils.this_function(), "Cannot make NamespaceTag itself's child")
        return child

    @validates('parent')
    def validate_parent(self, key, alias):
        # point to the original nstag
        if alias and alias.alias_for:
            alias = alias.alias_for

        # if self an alias, make original parent
        if self.alias_for:
            self.alias_for.parent = alias
            alias = None

        return alias

    @validates('tag')
    def validate_tag(self, key, alias):
        # point to the original
        if alias and alias.alias_for:
            alias = alias.alias_for
        return alias

    @validates('namespace')
    def validate_namespace(self, key, alias):
        # point to the original
        if alias and alias.alias_for:
            alias = alias.alias_for
        return alias

    def mapping_exists(self, obj=False, session=None):
        e = None
        sess = session or constants.db_session()

        if self.tag and self.tag.id:
            tag_id = self.tag.id
        else:
            tag_id = self.tag_id

        if self.namespace and self.namespace.id:
            namespace_id = self.namespace.id
        else:
            namespace_id = self.namespace_id

        if tag_id and namespace_id:
            e = sess.query(
                self.__class__).filter(
                and_op(
                    self.__class__.tag_id == tag_id,
                    self.__class__.namespace_id == namespace_id)).scalar()
        if not obj:
            e = True if e else False
        else:
            if not e:
                e = self
        return e

    def exists(self, *args, **kwargs):
        return self.mapping_exists(*args, **kwargs)

    @classmethod
    def unique_hash(cls, ns=None, tag=None):
        assert not isinstance(ns, Namespace)
        assert not isinstance(tag, Tag)
        if ns is None:
            ns = constants.special_namespace
        return (Namespace.format(ns), Tag.format(tag))

    @classmethod
    def unique_filter(cls, query, ns=None, tag=None):
        assert not isinstance(ns, Namespace)
        assert not isinstance(tag, Tag)
        if ns is None:
            ns = constants.special_namespace
        return query.join(cls.namespace).join(cls.tag).filter(and_op(Namespace.name == Namespace.format(ns),
                                                                     Tag.name == Tag.format(tag)))


metatag_association(NamespaceTags, "namespacetags")


@generic_repr
class Tag(LowerNameMixin, AliasMixin, Base):
    __tablename__ = 'tag'

    namespaces = relationship(
        "Namespace",
        secondary="namespace_tags",
        back_populates='tags',
        lazy="dynamic")

    @classmethod
    def format(cls, tag):
        if tag:
            return tag.lower()
        return tag


class Namespace(CapitalizedNameMixin, AliasMixin, Base):
    __tablename__ = 'namespace'

    tags = relationship(
        "Tag",
        secondary="namespace_tags",
        back_populates='namespaces',
        lazy="dynamic")

    @classmethod
    def default(cls):
        return Namespace.as_unique(name=constants.special_namespace)

    @classmethod
    def format(cls, ns):
        if ns:
            return ns.capitalize()
        return ns


taggable_tags = Table(
    'taggable_tags', Base.metadata,
    Column(
        'namespace_tag_id', Integer, ForeignKey('namespace_tags.id')),
    Column(
        'taggable_id', Integer, ForeignKey('taggable.id')),
    Column('timestamp', ArrowType, nullable=False, default=arrow.now),
    UniqueConstraint(
        'namespace_tag_id', 'taggable_id'))


class Taggable(UpdatedMixin, UserMixin, Base):
    __tablename__ = 'taggable'

    tags = relationship(
        "NamespaceTags",
        secondary=taggable_tags,
        lazy="dynamic")

    def compact_tags(self, tags):
        c_tags = {}
        for t in tags:
            c_tags.setdefault(t.namespace.name, []).append(t.tag.name)
        return c_tags


class TaggableMixin(UpdatedMixin):

    @declared_attr
    def taggable(cls):
        return relationship(
            "Taggable",
            single_parent=True,
            cascade="all, delete-orphan")

    @declared_attr
    def taggable_id(cls):
        return Column(Integer, ForeignKey('taggable.id'), nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.taggable = Taggable()

    @hybrid_property
    def tags(self):
        return self.taggable.tags

    compact_tags = Taggable.compact_tags


gallery_artists = Table(
    'gallery_artists', Base.metadata, Column(
        'artist_id', Integer, ForeignKey('artist.id')), Column(
            'gallery_id', Integer, ForeignKey('gallery.id')), UniqueConstraint(
                'artist_id', 'gallery_id'))

artist_circles = Table(
    'artist_circles', Base.metadata, Column(
        'circle_id', Integer, ForeignKey(
            'circle.id',)), Column(
                'artist_id', Integer, ForeignKey(
                    'artist.id',)), UniqueConstraint(
                        'circle_id', 'artist_id'))

artist_names = Table(
    'artist_names', Base.metadata, Column(
        'artistname_id', Integer, ForeignKey(
            'artistname.id',)), Column(
                'artist_id', Integer, ForeignKey(
                    'artist.id',)), UniqueConstraint(
                        'artistname_id', 'artist_id'))


@generic_repr
class ArtistName(NameMixin, AliasMixin, Base):
    __tablename__ = 'artistname'


@generic_repr
class Artist(UniqueMixin, ProfileMixin, UserMixin, Base):
    __tablename__ = 'artist'

    names = relationship(
        "ArtistName",
        secondary=artist_names,
        backref=backref("artists", lazy="dynamic"),
        cascade="all",
        lazy="joined")

    info = Column(Text, nullable=False, default='')

    galleries = relationship(
        "Gallery",
        secondary=gallery_artists,
        back_populates='artists',
        lazy="dynamic",
        cascade=default_cascade)

    circles = relationship(
        "Circle",
        secondary=artist_circles,
        back_populates='artists',
        lazy="joined",
        cascade=expunge_cascade)

    def __init__(self, *args, **kwargs):
        names = kwargs.pop("names", [])
        name = kwargs.pop("name", None)
        if name:
            names.append(name)
        super().__init__(*args, **kwargs)
        for n in names:
            n = ArtistName.as_unique(name=n)
            if n not in self.names:
                self.names.append(n)

    @classmethod
    def unique_hash(cls, name=None, names=None):
        n = []
        if name:
            n.append(name)
        if names:
            n.extend(names)
        return tuple(n)

    @classmethod
    def unique_filter(cls, query, name=None, names=None):
        n = []
        if name:
            n.append(name)
        if names:
            n.extend(names)
        return query.join(cls.names).filter(and_op(*(ArtistName.name == x for x in n)))


setup_preffered_name(Artist)
metatag_association(Artist, "artists")
profile_association(Artist, "artists")
url_association(Artist, "artists")


@generic_repr
class Circle(NameMixin, UserMixin, Base):
    __tablename__ = 'circle'

    artists = relationship(
        "Artist",
        secondary=artist_circles,
        back_populates='circles',
        lazy="dynamic")


gallery_parodies = Table(
    'gallery_parodies', Base.metadata, Column(
        'parody_id', Integer, ForeignKey('parody.id')), Column(
            'gallery_id', Integer, ForeignKey('gallery.id')), PrimaryKeyConstraint(
                'parody_id', 'gallery_id'))

parody_names = Table(
    'parody_names', Base.metadata, Column(
        'parodyname_id', Integer, ForeignKey(
            'parodyname.id',)), Column(
                'parody_id', Integer, ForeignKey(
                    'parody.id',)), UniqueConstraint(
                        'parodyname_id', 'parody_id'))


@generic_repr
class ParodyName(NameMixin, AliasMixin, Base):
    __tablename__ = 'parodyname'


@generic_repr
class Parody(UniqueMixin, ProfileMixin, UserMixin, Base):
    __tablename__ = 'parody'

    names = relationship(
        "ParodyName",
        secondary=parody_names,
        backref=backref("parodies", lazy="dynamic"),
        cascade="all",
        lazy="joined")

    galleries = relationship(
        "Gallery",
        secondary=gallery_parodies,
        back_populates='parodies',
        lazy="dynamic")

    def __init__(self, *args, **kwargs):
        names = kwargs.pop("names", [])
        name = kwargs.pop("name", None)
        if name:
            names.append(name)
        super().__init__(*args, **kwargs)
        for n in names:
            n = ParodyName.as_unique(name=n)
            if n not in self.names:
                self.names.append(n)

    @classmethod
    def unique_hash(cls, name=None, names=None):
        n = []
        if name:
            n.append(name)
        if names:
            n.extend(names)
        return tuple(n)

    @classmethod
    def unique_filter(cls, query, name=None, names=None):
        n = []
        if name:
            n.append(name)
        if names:
            n.extend(names)
        return query.join(cls.names).filter(and_op(*(ParodyName.name == x for x in n)))


setup_preffered_name(Parody)
profile_association(Parody, "parodies")

gallery_filters = Table('gallery_filters', Base.metadata,
                        Column('filter_id', Integer, ForeignKey('filter.id')),
                        Column(
                            'gallery_id',
                            Integer,
                            ForeignKey('gallery.id')),
                        Column('timestamp', ArrowType, nullable=False, default=arrow.now),
                        UniqueConstraint('filter_id', 'gallery_id'))


@generic_repr
class GalleryFilter(UserMixin, NameMixin, Base):
    __tablename__ = 'filter'
    filter = Column(Text, nullable=False, default='')
    enforce = Column(Boolean, nullable=False, default=False)
    regex = Column(Boolean, nullable=False, default=False)
    l_case = Column(Boolean, nullable=False, default=False)
    strict = Column(Boolean, nullable=False, default=False)

    galleries = relationship(
        "Gallery",
        secondary=gallery_filters,
        back_populates='filters',
        lazy="dynamic")


@generic_repr
class Status(NameMixin, UserMixin, Base):
    __tablename__ = 'status'

    names = clsutils.AttributeDict({
        'completed': 'Completed',
        'ongoing': 'Ongoing',
        'unreleased': 'Unreleased',
        'unknown': 'Unknown',
    })

    groupings = relationship(
        "Grouping",
        lazy='dynamic',
        back_populates='status')


@generic_repr
class Grouping(ProfileMixin, NameMixin, Base):
    __tablename__ = 'grouping'
    status_id = Column(Integer, ForeignKey('status.id'))

    galleries = relationship(
        "Gallery",
        back_populates="grouping",
        order_by="Gallery.number",
        lazy="dynamic",
        cascade="all, delete-orphan")
    status = relationship(
        "Status",
        back_populates="groupings",
        cascade=expunge_cascade)


profile_association(Grouping, "groupings")


@generic_repr
class Language(NameMixin, UserMixin, Base):
    __tablename__ = 'language'

    code = Column(LowerCaseString, nullable=False, default='')

    galleries = relationship(
        "Gallery",
        lazy='dynamic',
        back_populates='language')

    @validates("name")
    def validate_name(self, key, name):
        name, code = self._real_name(name)
        if code:
            self.code = code
        return name

    @classmethod
    def _real_name(cls, name):
        code = ''
        try:
            l = langcodes.find(name)
            name = utils.capitalize_text(l.autonym())
            code = l.language
        except LookupError:
            pass
        return name, code

    @validates("code")
    def validate_code(self, key, code):
        return utils.get_language_code(code)

    @classmethod
    def as_unique(cls, *arg, session=None, **kw):
        if 'name' in kw:
            name, _ = cls._real_name(kw['name'])
            kw['name'] = name
        return super().as_unique(*arg, session=session, **kw)


@generic_repr
class Category(NameMixin, UserMixin, Base):
    __tablename__ = 'category'

    galleries = relationship(
        "Gallery",
        lazy='dynamic',
        back_populates='category')


gallery_collections = Table(
    'gallery_collections', Base.metadata, Column(
        'collection_id', Integer, ForeignKey('collection.id')), Column(
            'gallery_id', Integer, ForeignKey('gallery.id')), Column(
                'timestamp', ArrowType, nullable=False, default=arrow.now),
    UniqueConstraint('collection_id', 'gallery_id'))


@generic_repr
class Collection(ProfileMixin, UpdatedMixin, NameMixin, UserMixin, Base):
    __tablename__ = 'collection'

    info = Column(Text, nullable=False, default='')
    pub_date = Column(ArrowType)
    category_id = Column(Integer, ForeignKey('category.id'))
    timestamp = Column(ArrowType, nullable=False, default=arrow.now)

    category = relationship(
        "Category",
        cascade=expunge_cascade)

    galleries = relationship(
        "Gallery",
        secondary=gallery_collections,
        order_by=desc_expr(gallery_collections.c.timestamp),
        back_populates="collections",
        lazy="dynamic",
        cascade=default_cascade)


profile_association(Collection, "collections")
metatag_association(Collection, "collections")


@generic_repr
class Gallery(TaggableMixin, ProfileMixin, Base):
    __tablename__ = 'gallery'

    last_read = Column(ArrowType)
    pub_date = Column(ArrowType)
    info = Column(Text, nullable=False, default='')
    single_source = Column(Boolean, default=True)
    phantom = Column(Boolean, default=False)
    rating = Column(Integer, nullable=False, default=0)
    times_read = Column(Integer, nullable=False, default=0)
    timestamp = Column(ArrowType, nullable=False, default=arrow.now)
    number = Column(Integer, nullable=False, default=0)
    category_id = Column(Integer, ForeignKey('category.id'))
    language_id = Column(Integer, ForeignKey('language.id'))
    grouping_id = Column(Integer, ForeignKey('grouping.id'))

    grouping = relationship(
        "Grouping",
        back_populates="galleries",
        cascade=expunge_cascade)
    collections = relationship(
        "Collection",
        secondary=gallery_collections,
        back_populates="galleries",
        cascade=expunge_cascade,
        lazy="dynamic")
    language = relationship(
        "Language",
        back_populates="galleries",
        cascade=expunge_cascade)
    category = relationship(
        "Category",
        back_populates="galleries",
        cascade=expunge_cascade)
    artists = relationship(
        "Artist",
        secondary=gallery_artists,
        back_populates='galleries',
        lazy="joined",
        cascade=expunge_cascade)
    filters = relationship(
        "GalleryFilter",
        secondary=gallery_filters,
        back_populates='galleries',
        lazy="dynamic")
    pages = relationship(
        "Page",
        order_by="Page.number",
        query_class=OrderingQuery,
        back_populates="gallery",
        lazy='dynamic',
        cascade="all,delete-orphan")
    titles = relationship(
        "Title",
        back_populates="gallery",
        lazy='joined',
        cascade="all,delete-orphan")
    parodies = relationship(
        "Parody",
        secondary=gallery_parodies,
        back_populates='galleries',
        lazy="joined",
        cascade=expunge_cascade)

    first_page = relationship(lambda: Page,
                              primaryjoin=lambda: and_op(
                                  Gallery.id == Page.gallery_id,
                                  Page.number == select([func.min(Page.number)]).
                                  where(Page.gallery_id == Gallery.id).
                                  correlate(Gallery.__table__)
                              ),
                              uselist=False,
                              )

    def read(self, user_id=None, datetime=None):
        "Creates a read event for user"
        if not datetime:
            datetime = arrow.now()
        if user_id is None:
            user_id = UserMixin.current_user()
        self.last_read = datetime
        sess = object_session(self)
        if sess:
            sess.add(Event(Event.Action.gallery_read, self, user_id=user_id, timestamp=datetime))
        else:
            log.w(
                "Cannot add gallery read event because no session exists for this object")
        self.times_read += 1
        self.last_read = datetime
        for m in self.metatags:
            if m.name == MetaTag.names.read:
                break
        else:
            m = MetaTag.as_unique(name=MetaTag.names.read, session=sess)
            self.metatags.append(m)

    @hybrid_property
    def preferred_title(self):
        t = self.title_by_language(config.translation_locale.value)
        if not t and self.titles:
            t = self.titles[0]
        return t

    @preferred_title.setter
    def preferred_title(self, title):
        pref_title = self.preferred_title
        assert pref_title, "This gallery has no titles"
        if not isinstance(title, Title):
            title = Title()
            title.gallery = self
            title.name = title
            lcode = config.translation_locale.value
            title.language = Language(lcode)
        pref_title.replace_with(title)
        pref_title.gallery = self

    @preferred_title.expression
    def preferred_title(cls):
        lcode = utils.get_language_code(config.translation_locale.value)
        j = Title.__table__.join(Language.__table__, Title.__table__.c.language_id == Language.__table__.c.id)
        return select([Title]).select_from(j).where(Title.gallery_id == cls.id).where(
            Language.code == lcode).label("preffered_title")

    @hybrid_method
    def title_by_language(self, language_code):
        language_code = utils.get_language_code(language_code)
        for t in self.titles:
            if t.language and t.language.code == language_code:
                return t

    def get_sources(self):
        ""
        p_paths = []
        if self.id:
            ensure_in_session(self)
            if self.gallery.single_source:
                p_path = constants.db_session().query(Page.path).filter(Page.gallery_id == self.id,
                                                                        Page.number == 1)
                if p_path:
                    p_paths.append(str(pathlib.Path(p_path).parent))
            else:
                raise NotImplementedError
        return tuple(p_paths)

    @classmethod
    def exists_by_path(cls, path="", obj=False, case=True):
        """Checks if gallery exists by path
        """
        assert path
        path = Page.format_path(path)
        e = False
        s = constants.db_session()
        with s.no_autoflush:
            page_expr = Page.path.like if case else Page.path.ilike
            page_expr = page_expr(path + '%')
            if obj:
                e = s.query(Gallery).join(Gallery.pages).filter(page_expr).first()
            else:
                e = bool(s.query(Page.id).filter(page_expr).count())
            return e


metatag_association(Gallery, "galleries")
profile_association(Gallery, "galleries")
url_association(Gallery, "galleries")


@generic_repr
class Page(TaggableMixin, ProfileMixin, Base):
    __tablename__ = 'page'
    number = Column(Integer, nullable=False, index=True, default=-1)
    name = Column(String, nullable=False, default='')
    path = Column(Text, nullable=False, default='')
    hash_id = Column(Integer, ForeignKey('hash.id'))
    gallery_id = Column(Integer, ForeignKey('gallery.id'), nullable=False)
    in_archive = Column(Boolean, default=False)
    timestamp = Column(ArrowType, nullable=False, default=arrow.now)

    hash = relationship("Hash", cascade=expunge_cascade)
    gallery = relationship("Gallery", back_populates="pages")

    @validates('path')
    def _validate_path(self, key, p):
        return self.format_path(p)

    @classmethod
    def format_path(cls, path):
        return str(pathlib.Path(path))

    @property
    def file_type(self):
        ext = ''
        if self.path:
            _, ext = os.path.splitext(self.path)
        return ext.lower()

    def exists(self, obj=False):
        """Checks if page exist by path
        Params:
            obj -- queries for the full object and returns it
        """
        e = self
        if not constants.db_session:
            return e
        sess = constants.db_session()
        with sess.no_autoflush:
            p = self.__class__
            if self.path:
                e = sess.query(
                    p.id).filter(
                    and_(
                        p.path.like(
                            "{}".format(
                                self.path)))).scalar()
                if not obj:
                    e = e is not None
            else:
                log.w("Could not query for page existence because no path was set.")
            return e


metatag_association(Page, "pages")
profile_association(Page, "pages")


@generic_repr
class Title(AliasMixin, UserMixin, Base):
    __tablename__ = 'title'
    name = Column(String, nullable=False, default="")  # OBS: not unique
    language_id = Column(Integer, ForeignKey('language.id'))
    gallery_id = Column(Integer, ForeignKey('gallery.id'), nullable=False)

    language = relationship(
        "Language",
        cascade=expunge_cascade)
    gallery = relationship("Gallery", back_populates="titles")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


@generic_repr
class Url(UserMixin, Base):
    __tablename__ = 'url'
    name = Column(Text, nullable=False, default='')  # OBS: not unique


@generic_repr
class MetaList(UserMixin, NameMixin, Base):
    __tablename__ = 'metalist'


metalist_mappers = [x for x in globals().values() if
                    pyinspect.isclass(x) and issubclass(x, Base) and
                    x not in (Base, MetaList)]

for y in metalist_mappers:
    metalist_association(y, y.__tablename__ + 's')

# =======================================================================================

# Note: necessary to put in function because there is no Session object yet


def initEvents(sess):
    "Initializes events"

    @event.listens_for(sess, 'after_flush')
    def aliasmixin_delete(s, ctx):
        "when root is deleted, delete all its aliases"

        with safe_session(s) as session:
            found = [obj for obj in session.deleted if isinstance(obj, AliasMixin) and obj.aliases]
            for a in found:
                for x in a.aliases:
                    x.delete()

    @event.listens_for(Taggable.tags, 'append', retval=True)
    def taggable_new_tag(target, value, initiator):
        "when a tag is added, add its forefathers too"
        target.last_updated = arrow.now()

        # only add the original nstag
        if value and value.alias_for:
            target.tags.remove(value)
            value = value.alias_for
            if value not in target.tags:
                target.tags.append(value)

        if value and value.parent:
            if value.parent not in target.tags:
                target.tags.append(value.parent)

        return value

    @event.listens_for(Taggable.tags, 'remove')
    def taggable_remove_tag(target, value, initiator):
        "when a tag is removed, remove its children too"
        target.last_updated = arrow.now()

        if value and len(value.children):
            if initiator.op:
                initiator.op = None
                for c in value.children:
                    target.tags.remove(c)

    @event.listens_for(UpdatedMixin, 'before_update', propagate=True)
    def timestamp_before_update(mapper, connection, target):
        target.last_updated = arrow.now()

    def many_to_many_deletion(cls, attr=None, custom_filter=None, found_attrs=lambda: []):

        def mtom(s, ctx):
            orphans_found = True

            #f_attrs = found_attrs()

            # if attr:
            #    f_attrs.append(attr())

            # if f_attrs:
            #    try:
            #        orphans_found = (
            #            any(isinstance(obj, cls) and
            #                any(attributes.get_history(obj, x.key).deleted for x in f_attrs)
            #                for obj in s.dirty) or
            #            any(isinstance(obj, cls) for obj in s.deleted)
            #            )
            #    except KeyError:
            #        pass

            if orphans_found:
                if custom_filter:
                    cfilter = custom_filter()
                else:
                    cfilter = ~(attr()).any()
                with safe_session(s) as session:
                    session.query(cls).filter(cfilter).delete(synchronize_session=False)

        event.listen(sess, 'after_flush', mtom)

    many_to_many_deletion(Artist, lambda: Artist.galleries)
    many_to_many_deletion(Parody, lambda: Parody.galleries)
    many_to_many_deletion(Grouping, lambda: Grouping.galleries)
    many_to_many_deletion(Tag, lambda: Tag.namespaces)
    many_to_many_deletion(Namespace, lambda: Namespace.tags)
    many_to_many_deletion(Circle, lambda: Circle.artists)
    many_to_many_deletion(ArtistName, custom_filter=lambda: and_op(
        ArtistName.alias_for == None,  # noqa: E711
        ~ArtistName.artists.any(),
    ), found_attrs=lambda: [ArtistName.artists])
    many_to_many_deletion(ParodyName, custom_filter=lambda: and_op(
        ParodyName.alias_for == None,  # noqa: E711
        ~ParodyName.parodies.any(),
    ), found_attrs=lambda: [ParodyName.parodies])
    # TODO: clean up
    many_to_many_deletion(Profile, custom_filter=lambda: and_op(
        ~Profile.artists.any(),
        ~Profile.collections.any(),
        ~Profile.groupings.any(),
        ~Profile.pages.any(),
        ~Profile.galleries.any()),
        found_attrs=lambda: [Profile.artists,
                             Profile.collections,
                             Profile.groupings,
                             Profile.pages,
                             Profile.galleries])
    many_to_many_deletion(Url, custom_filter=lambda: and_op(
        ~Url.artists.any(),
        ~Url.galleries.any()),
        found_attrs=lambda: [Url.artists, Url.galleries])
    many_to_many_deletion(NamespaceTags, custom_filter=lambda: or_op(
        NamespaceTags.tag == None,  # noqa: E711
        NamespaceTags.namespace == None),  # noqa: E711
        found_attrs=lambda: [NamespaceTags.tag, NamespaceTags.namespace])


@compiles(RegexMatchExpression, 'sqlite')
def sqlite_regex_match(element, compiler, **kw):
    """Compile the SQL expression representing a regular expression match
    for the SQLite engine.
    """
    # determine the name of a custom SQLite function to use for the operator
    operator = element.operator.opstring
    try:
        func_name, _ = SQLITE_REGEX_FUNCTIONS[operator]
    except (KeyError, ValueError) as e:
        would_be_sql_string = ' '.join((compiler.process(element.left),
                                        operator,
                                        compiler.process(element.right)))
        raise exc.StatementError(
            "unknown regular expression match operator: %s" %
            operator, would_be_sql_string, None, e)

    # compile the expression as an invocation of the custom function
    regex_func = getattr(func, func_name)
    regex_func_call = regex_func(element.left, element.right)
    return compiler.process(regex_func_call)


@event.listens_for(Engine, 'connect')
def engine_connect(dbapi_connection, connection_record):

    if config.dialect.value == constants.Dialect.SQLITE:
        for name, function in SQLITE_REGEX_FUNCTIONS.values():
            dbapi_connection.create_function(name, 2, function)

        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA case_sensitive_like = 1;")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()
    elif config.dialect.value == constants.Dialect.POSTGRES:
        cursor = dbapi_connection.cursor()
        cursor.execute("SHOW server_version_num;")
        if int(cursor.fetchone()[0]) < 90400:
            raise exceptions.DatabaseInitError("HPX requires Postgres version 9.4 and up")
        cursor.close()


def init_defaults(sess, first_time=True):
    "Initializes default items"
    # init default user
    duser = sess.query(User).filter(
        User.role == User.Role.default).one_or_none()
    if not duser:
        duser = User(name=constants.super_user_name, role=User.Role.default)
        sess.add(duser)
    constants.default_user = duser
    # init default metatags
    for t in MetaTag.names:
        t_d = sess.query(MetaTag).filter(MetaTag.name == t).one_or_none()
        if not t_d:
            t_d = MetaTag(name=t)
            sess.add(t_d)
        MetaTag.tags[t] = t_d

    # init status
    if first_time:
        for s in Status.names.values():
            db_st = Status()
            db_st.name = s
            if not db_st.exists(session=sess):
                sess.add(db_st)
    sess.commit()


def create_user(role, name=None, password=None):
    """
    Create user
    role:
        - default -- create a default user with no password if it doesnt exist
        - admin -- create admin user
        - user -- create regular user
    """
    assert isinstance(role, User.Role)

    s = constants.db_session()

    if role == User.Role.default:
        if not s.query(User.id).filter(User.name == constants.super_user_name).one_or_none():
            s.add(User(name=constants.super_user_name, role=User.Role.default))
            s.commit()
            return True

    elif role == User.Role.guest:
        if not s.query(User.id).filter(User.name == name).one_or_none():
            s.add(User(name=name,
                       role=User.Role.guest))
            s.commit()
            return True
    elif role == User.Role.user:
        if not s.query(User.id).filter(User.name == name).one_or_none():
            s.add(User(name=name,
                       role=User.Role.user,
                       password=password))
            s.commit()
            return True
    elif role == User.Role.admin:
        if not s.query(User.id).filter(User.name == name).one_or_none():
            s.add(User(name=name,
                       password=PasswordHash.new(password, 12),
                       role=User.Role.admin))
            s.commit()
            return True


def delete_user(name=None):
    """
    Delete user
    """
    if not name == "default":
        s = constants.db_session()
        u = s.query(User).filter(User.name == name).one_or_none()
        if u:
            s.delete(u)
            s.commit()
            return True
    return False


def list_users(role=None, limit=100, offset=0):
    assert role is None or isinstance(role, User.Role)
    s = constants.db_session()
    q = s.query(User).filter(User.name != constants.super_user_name).order_by(User.name)
    if role:
        q.filter(User.role == role)
    return q.offset(offset).limit(limit).all()


def check_db_version(sess):
    """Checks if DB version"""
    try:
        life = sess.query(Life).one_or_none()
    except (exc.NoSuchTableError, exc.OperationalError):
        if constants.preview:
            msg = 'Incompatible database. Please generate a new database using the HPtoHPX tool.'
            log.w(msg, stdout=True)
            return False
        else:
            raise exceptions.DatabaseInitError(
                "Invalid database. Momo says she thinks this database is not HPX-compatible.")
    if life:
        if life.version != constants.version_db_str:
            if constants.preview:
                msg = 'Incompatible database. Please generate a new database using the HPtoHPX tool.'
                log.w(msg, stdout=True)
                return False
            else:
                msg = 'Found database version {}. Your database has been upgraded/downgraded to version {}.'.format(
                    life.version, constants.version_db_str)
                log.i(msg, stdout=True)
    else:
        life = Life()
        sess.add(life)
        life.version = constants.version_db_str
        life.times_opened = 0

    db_key = "db_usage"

    life.times_opened += 1

    idb = constants.internaldb
    if db_key not in idb or idb[db_key] + 1 != life.times_opened:
        constants.is_new_db = True
        constants.invalidator.similar_gallery = True
    idb[db_key] = life.times_opened

    log.d("Using DB Version: {}".format(life.version))

    init_defaults(sess, life.times_opened == 1)
    log.d("Succesfully initiated database")
    sess.commit()
    return True


def _get_session(sess):
    utils.switch(constants.Priority.Normal)
    return sess()


def _get_current():
    if not utils.in_cpubound_thread() and constants.server_started:
        l_obj = gevent.getcurrent()
    else:
        l_obj = threading.current_thread()
    return l_obj


def make_db_url(db_name=None, dev_db=None):
    if dev_db is None:
        dev_db = constants.dev_db
    if db_name is None:
        db_name = constants.db_name_dev if dev_db and config.db_name.value == constants.db_name else config.db_name.value
    db_query = {}
    if config.dialect.value == constants.Dialect.MYSQL:
        db_query.update({'charset': 'utf8mb4'})
    db_query.update(config.db_query.value)
    drivername = config.dialect.value
    if drivername == constants.Dialect.MYSQL:
        drivername += '+pymysql'

    if drivername == constants.Dialect.SQLITE:
        db_url = sa_make_url(os.path.join("sqlite:///", constants.db_path_dev if dev_db else constants.db_path))
    else:
        db_url = URL(
            drivername,
            username=config.db_username.value,
            password=config.db_password.value,
            host=config.db_host.value,
            port=config.db_port.value,
            database=db_name,
            query=db_query,
        )
    return db_url


def migrate():
    if hasattr(sys, "_called_from_test"):
        return
    log.i("Checking for database update", stdout=True)
    a_cfg = alembic.config.Config(constants.migration_config_path)
    a_cfg.attributes['configure_logger'] = False
    script = alembic.script.ScriptDirectory.from_config(a_cfg)
    ctx = alembic.migration.MigrationContext.configure(constants.db_engine.connect())
    log.d("Database BASE revision:", tuple(script.get_bases()))
    current_rev = tuple(ctx.get_current_heads())
    head_rev = tuple(script.get_heads())
    log.d("Database current revision:", current_rev)
    log.d("Database HEAD revision:", head_rev)
    if current_rev != head_rev:
        log.i("Database update found. Updating...", stdout=True)
    alembic.command.upgrade(a_cfg, "head")
    if current_rev != head_rev:
        log.i("Database has been updated!", stdout=True)


def init(**kwargs):
    log.i("Using", config.dialect.value, "database", stdout=True)
    db_path = kwargs.get("path")
    if not db_path:
        db_path = constants.db_path_dev if constants.dev_db else constants.db_path
    Session = scoped_session(sessionmaker(), scopefunc=_get_current)
    constants._db_scoped_session = Session
    constants.db_session = functools.partial(_get_session, Session)
    initEvents(Session)
    constants.db_engine = kwargs.get("engine")
    db_encoding = 'utf8mb4' if config.dialect.value == constants.Dialect.MYSQL else 'utf8'
    try:
        if not constants.db_engine:
            if config.dialect.value == constants.Dialect.SQLITE:
                constants.db_engine = create_engine(os.path.join("sqlite:///", db_path),
                                                    connect_args={'timeout': config.sqlite_database_timeout.value,
                                                                  'check_same_thread': False})
            else:
                db_url = make_db_url()
                if not database_exists(db_url):
                    create_database(db_url, db_encoding)
                constants.db_engine = create_engine(db_url, max_overflow=20,
                                                    pool_size=config.pool_size.value,
                                                    pool_timeout=config.pool_timeout.value)

        Base.metadata.create_all(constants.db_engine)

        migrate()

        Session.configure(bind=constants.db_engine)
    except exc.OperationalError as e:
        raise exceptions.DatabaseInitError("{}".format(e.orig))
    except exc.ProgrammingError as e:
        if config.dialect.value == constants.Dialect.POSTGRES and 'server_version_num' in str(e):
            raise exceptions.DatabaseInitError("HPX requires Postgres version 9.4 and up")

    return check_db_version(Session())


def add_bulk(session, objects, amount=100, flush=False, bulk_save=False, return_defaults=True):
    """
    Add objects in a bulk of x amount
    """
    left = objects[:amount]
    while left:
        session.bulk_save_objects(left, return_defaults=return_defaults) if bulk_save else session.add_all(left)
        session.flush() if flush else session.commit()
        objects = objects[amount:]
        left = objects[:amount]


def table_attribs(model, id=False, descriptors=False, raise_err=True, exclude=tuple(), allow=tuple()):
    """Returns a dict of table column names and their SQLAlchemy value objects
    Params:
        id -- retrieve id columns instead of the sqlalchemy object (to avoid a db query etc.)
        descriptors -- include hybrid attributes and association proxies
    """
    assert isinstance(model, Base) or issubclass(model, Base), f"{model}"
    exclude = tuple(exclude)
    d = {}
    obj = model
    in_obj = inspect(model)
    if isinstance(in_obj, state.InstanceState):
        sess = object_session(model)
        model = type(obj)
        with no_autoflush(sess):
            attr = list(in_obj.attrs)

            if id is None:
                ex = tuple()
            else:
                ex = tuple(y.key for y in attr if y.key.endswith('_id') and y.key[:-3] not in allow)
                if id:
                    ex = tuple(x[:-3] for x in ex)  # -3 for '_id'

            exclude += ex

            for x in attr:
                if x.key not in exclude:
                    try:
                        d[x.key] = x.value
                    except exc_orm.DetachedInstanceError:
                        if raise_err:
                            raise
                        d[x.key] = None
    else:
        for name in model.__dict__:
            if name in exclude:
                continue
            value = model.__dict__[name]
            if isinstance(value, attributes.InstrumentedAttribute):
                d[name] = value

    if descriptors:
        for name, value in model.__dict__.items():
            if name not in exclude and isinstance(value, (hybrid_property, AssociationProxy, index_property)):
                try:
                    if pyinspect.isclass(obj):
                        d[name] = value
                    else:
                        d[name] = getattr(obj, name)
                except exc_orm.DetachedInstanceError:
                    if raise_err:
                        raise
                    d[name] = None
    return d


def is_detached(obj):
    "Check if obj was expunged from a session"
    if is_instanced(obj):
        return inspect(obj).detached


def is_instanced(obj):
    "Check if db object is an instanced object"
    if isinstance(obj, Base):
        return isinstance(inspect(obj), state.InstanceState)
    return False


def is_descriptor(obj):
    "Check if db object is a descriptor"
    if isinstance(obj, (hybrid_property, AssociationProxy, index_property)):
        return True
    return False


def descriptor_has_getter(obj):
    "Check if db object is descriptor has a getter"
    assert is_descriptor(obj) and not isinstance(obj, AssociationProxy)
    return True if obj.fget else False


def descriptor_has_setter(obj):
    "Check if db object is descriptor has a setter"
    assert is_descriptor(obj) and not isinstance(obj, AssociationProxy)
    return True if obj.fset else False


def is_list(obj, strict=False):
    "Check if db object is a db list"
    if not strict and isinstance(obj, attributes.InstrumentedAttribute):
        if isinstance(obj.property, properties.RelationshipProperty):
            if obj.property.uselist and obj.property.lazy not in ('dynamic',):
                return True
    return isinstance(obj, collections.InstrumentedList)


def is_query(obj, strict=False):
    "Check if db object is a dynamic query object (issued by lazy='dynamic')"
    if not strict and isinstance(obj, attributes.InstrumentedAttribute):
        if isinstance(obj.property, properties.RelationshipProperty):
            if obj.property.lazy in ('dynamic',):
                return True
    return isinstance(obj, dynamic.AppenderQuery)


def related_classes(obj):
    "Returns a list of mapper classes that has a relationship with given mapper class"
    assert issubclass(obj, Base)

    return [x.mapper.class_ for x in inspect(obj).relationships]


def relationship_column(objA, objB):
    "Return model attribute on objA that has a relationship with objB"
    assert issubclass(objA, Base)
    assert issubclass(objB, Base)

    rel = related_classes(objA)

    if objB not in rel:
        return None

    for c in table_attribs(objA).values():
        if get_type(c) == objB:
            return c


def column_model(obj):
    "Return model class for given model attribute/column"
    try:
        return get_type(obj)
    except TypeError:
        raise TypeError(f"Couldn't inspect type: {obj}")


def column_name(obj):
    "Return name of model attribute for given model attribute"
    raise NotImplementedError


def model_name(model):
    "Return name of model"
    assert issubclass(model, Base)
    return model.__name__


def ensure_in_session(item, session=None):
    """
    Ensures item is in a session, returns item
    """
    if not object_session(item):
        try:
            session = session or constants.db_session()
            session.add(item)
            return item
        except exc.InvalidRequestError:
            return constants.db_session().merge(item)
    return item


def freeze_object(obj):
    if is_instanced(obj):
        sess = object_session(obj)
        if sess:
            with sess.no_autoflush:
                for t, v in table_attribs(obj, descriptors=True, raise_err=False).items():
                    if is_instanced(v):
                        freeze_object(v)
                    elif is_list(v):
                        for x in v:
                            freeze_object(v)
                try:
                    sess.refresh(obj)
                except exc.InvalidRequestError:
                    pass
                sess.expunge(obj)
    return obj


@contextmanager
def safe_session(sess=None):
    if not sess:
        sess = constants._db_scoped_session.session_factory()
    with sess.no_autoflush:
        try:
            yield sess
        except sa_exc.OperationalError as e:
            log.exception("Exception raised in non-scoped db session")
            if "database is locked" not in str(e):
                raise


@contextmanager
def cleanup_session():
    try:
        yield
    finally:
        constants._db_scoped_session.remove()


def cleanup_session_wrap(f=None):
    if f is None:
        def p_wrap(f):
            return cleanup_session_wrap(f)
        return p_wrap
    else:

        def wrapper(*args, **kwargs):
            with cleanup_session():
                return f(*args, **kwargs)
        return wrapper


@contextmanager
def no_autoflush(sess=None):
    if sess:
        o = sess.autoflush
        sess.autoflush = False
    try:
        yield sess
    finally:
        if sess:
            sess.autoflush = o
