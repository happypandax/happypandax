from sqlalchemy.engine import Engine
from sqlalchemy import String as _String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import BinaryExpression, func, literal
from sqlalchemy.sql.operators import custom_op
from sqlalchemy.orm import sessionmaker, relationship, validates, object_session, scoped_session
from sqlalchemy import (create_engine, event, exc, and_, or_, Boolean, Column, Integer, ForeignKey,
                        Table, Date, DateTime, UniqueConstraint, Float)
from dateutil import parser as dateparser

import datetime
import logging
import os
import random

from happypanda.common import constants, exceptions


log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

class String(_String):
    """Enchanced version of standard SQLAlchemy's :class:`String`.
    Supports additional operators that can be used while constructing
    filter expressions.
    """
    class comparator_factory(_String.comparator_factory):
        """Contains implementation of :class:`String` operators
        related to regular expressions.
        """
        def regexp(self, other):
            return RegexMatchExpression(self.expr, literal(other), custom_op('~'))

        def iregexp(self, other):
            return RegexMatchExpression(self.expr, literal(other), custom_op('~*'))

        def not_regexp(self, other):
            return RegexMatchExpression(self.expr, literal(other), custom_op('!~'))

        def not_iregexp(self, other):
            return RegexMatchExpression(self.expr, literal(other), custom_op('!~*'))


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

class BaseID:
    id = Column(Integer, primary_key=True)

    def delete(self):
        sess = object_session(self)
        if not sess:
            sess = constants.db_session()
        sess.delete(self)
        return sess

class NameMixin:
    name = Column(String, nullable=False, default='', unique=True)

    def exists(self, full=False, strict=False):
        "Full: queries for the full object and returns it"
        sess = constants.db_session()
        if full:
            if strict:
                e = sess.query(self.__class__).filter_by(name=self.name).scalar()
            else:
                e = sess.query(self.__class__).filter(self.__class__.name.ilike("{}".format(self.name))).scalar()
            if not e:
                e = self
        else:
            if strict:
                e = sess.query(self.__class__.id).filter_by(name=self.name).scalar() is not None
            else:
                e = sess.query(self.__class__.id).filter(self.__class__.name.ilike("{}".format(self.name))).scalar() is not None
        sess.close()
        return e

    def __repr__(self):
        return "<{}(ID: {}, Name: {})>".format(self.__class__.__name__, self.id, self.name)

class ProfileMixin:

    def get_profile(self, profile_type):
        return ''

Base = declarative_base(cls=BaseID)

def validate_int(value):
    if isinstance(value, str):
        try:
            value = int(value)
        except:
            raise AssertionError("Column only accepts integer, not {}".format(type(value)))
    else:
        assert isinstance(value, int) or value is None, "Column only accepts integer, not {}".format(type(value))
    return value

def validate_string(value):
    assert isinstance(value, str) or value is None, "Column only accepts string, not {}".format(type(value))
    return value

def validate_datetime(value):
    assert isinstance(value, datetime.datetime) or value is None, "Column only accepts datetime, not {}".format(type(value))
    return value

def validate_date(value):
    assert isinstance(value, datetime.date) or value is None, "Column only accepts date, not {}".format(type(value))
    return value

def validate_bool(value):
    assert isinstance(value, bool) or value is None, "Column only accepts boolean, not {}".format(type(value))
    return value

validators = {
    Integer:validate_int,
    String:validate_string,
    DateTime:validate_datetime,
    Date:validate_date,
    Boolean:validate_bool,
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

def profile_association(table_name):
    column = '{}_id'.format(table_name)
    assoc = Table('{}_profiles'.format(table_name), Base.metadata,
                        Column('profile_id', Integer, ForeignKey('profile.id')),
                        Column(column, Integer, ForeignKey('{}.id'.format(table_name))),
                        UniqueConstraint('profile_id', column))
    return assoc

class Life(Base):
    __tablename__ = 'life'

    version = Column(Float, nullable=False, default=constants.db_version,)
    times_opened = Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return "<Version: {}, times_opened:{}>".format(self.version, self.times_opened)

class Profile(Base):
    __tablename__ = 'profile'

    path = Column(String, nullable=False, default='')
    type = Column(Integer, nullable=False, default=0)

    def __repr__(self):
        return "Profile ID:{} Type:{} Path:{}".format(self.id, self.type, self.path)


class History(Base):
    __tablename__ = 'history'

    gallery_id = Column(Integer, ForeignKey('gallery.id'))
    date = Column(Date, nullable=False, default=datetime.date.today())
    gallery = relationship("Gallery")

    def __init__(self, gallery):
        self.gallery = gallery

class Hash(NameMixin, Base):
    __tablename__ = 'hash'

class NamespaceTags(Base):
    __tablename__ = 'namespace_tags'

    tag_id = Column(Integer, ForeignKey('tag.id'))
    namespace_id = Column(Integer, ForeignKey('namespace.id'))
    __table_args__ = (UniqueConstraint('tag_id', 'namespace_id'),)

    tag = relationship("Tag", cascade="save-update, merge, refresh-expire")
    namespace = relationship("Namespace", cascade="save-update, merge, refresh-expire")

    def mapping_exists(self):
        sess = constants.db_session()
        e = sess.query(self.__class__).filter_by(and_(tag_id=self.tag_id, namespace_id=self.namespace_id)).scalar()
        if not e:
            e = self
        sess.close()
        return e

    def __init__(self, ns, tag):
        self.namespace = ns
        self.tag = tag

class Tag(NameMixin, Base):
    __tablename__ = 'tag'

    namespaces = relationship("Namespace", secondary='namespace_tags', back_populates='tags', lazy="dynamic")

class Namespace(NameMixin, Base):
    __tablename__ = 'namespace'

    tags = relationship("Tag", secondary='namespace_tags', back_populates='namespaces', lazy="dynamic")

gallery_artists = Table('gallery_artists', Base.metadata,
                        Column('artist_id', Integer, ForeignKey('artist.id')),
                        Column('gallery_id', Integer, ForeignKey('gallery.id')),
                        UniqueConstraint('artist_id', 'gallery_id'))


class Artist(NameMixin, Base):
    __tablename__ = 'artist'

    galleries = relationship("Gallery", secondary=gallery_artists, back_populates='artists', lazy="dynamic")

gallery_circles = Table('gallery_circles', Base.metadata,
                        Column('circle_id', Integer, ForeignKey('circle.id',)),
                        Column('gallery_id', Integer, ForeignKey('gallery.id',)),
                        UniqueConstraint('circle_id', 'gallery_id'))

class Circle(NameMixin, Base):
    __tablename__ = 'circle'

    galleries = relationship("Gallery", secondary=gallery_circles, back_populates='circles', lazy="dynamic")

gallery_lists = Table('gallery_lists', Base.metadata,
                        Column('list_id', Integer, ForeignKey('list.id')),
                        Column('gallery_id', Integer, ForeignKey('gallery.id')),
                        UniqueConstraint('list_id', 'gallery_id'))

list_profiles = profile_association("list")

class List(ProfileMixin, NameMixin, Base):
    __tablename__ = 'list'
    filter = Column(String, nullable=False, default='')
    enforce = Column(Boolean, nullable=False, default=False)
    regex = Column(Boolean, nullable=False, default=False)
    l_case = Column(Boolean, nullable=False, default=False)
    strict = Column(Boolean, nullable=False, default=False)

    galleries = relationship("Gallery", secondary=gallery_lists, back_populates='lists', lazy="dynamic")
    profiles = relationship("Profile", secondary=list_profiles, cascade="all")

class Status(NameMixin, Base):
    __tablename__ = 'status'

    gnamespaces = relationship("GalleryNamespace", back_populates='status')

g_ns_profiles = profile_association("gallery_namespace")

class GalleryNamespace(ProfileMixin, NameMixin, Base):
    __tablename__ = 'gallery_namespace'
    status_id = Column(Integer, ForeignKey('status.id'))

    galleries = relationship("Gallery", back_populates="parent", lazy="dynamic", cascade="all, delete-orphan")
    profiles = relationship("Profile", secondary=g_ns_profiles, cascade="all")
    status = relationship("Status", back_populates="gnamespaces", cascade="save-update, merge, refresh-expire")

    def __repr__(self):
        return "ID:{} - G-Namespace:{}".format(self.id, self.name)

class Language(NameMixin, Base):
    __tablename__ = 'language'

    galleries = relationship("Gallery", back_populates='language')

class GalleryType(NameMixin, Base):
    __tablename__ = 'type'

    galleries = relationship("Gallery", back_populates='type')

gallery_tags = Table('gallery_tags', Base.metadata,
                        Column('namespace_tag_id', Integer, ForeignKey('namespace_tags.id')),
                        Column('gallery_id', Integer, ForeignKey('gallery.id')),
                        UniqueConstraint('namespace_tag_id', 'gallery_id'))

collection_profiles = profile_association("collection")

class Collection(ProfileMixin, Base):
    __tablename__ = 'collection'
    title = Column(String, nullable=False, default='')
    info = Column(String, nullable=False, default='')
    cover = Column(String, nullable=False, default='')

    galleries = relationship("Gallery", back_populates="collection", cascade="save-update, merge, refresh-expire")
    profiles = relationship("Profile", secondary=collection_profiles, cascade="all")

    @property
    def rating(self):
        "Calculates average rating from galleries"
        return 5

    @classmethod
    def search(cls, key, args=[], session=None):
        "Check if gallery contains keyword"
        if not session:
            session = constants.db_session()
        q = session.query(cls.id)
        if key:
            is_exclude = False if key[0] == '-' else True
            key = key[1:] if not is_exclude else key
            helper = utils._ValidContainerHelper()
            if not ':' in key:
                for g_attr in [cls.title, cls.info]:
                    if app_constants.Search.Regex in args:
                        helper.add(q.filter(g_attr.ilike(key)).all())
                    else:
                        helper.add(q.filter(g_attr.ilike("%{}%".format(key))).all())

            return helper.done()
        else:
            ids = q.all()
            return ids if ids else None

    def __repr__(self):
        return "ID:{} - Collection Title:{}\nCollection Cover:{}".format(self.id, self.title, self.cover)

gallery_profiles = profile_association("gallery")

class Gallery(ProfileMixin, Base):
    __tablename__ = 'gallery'
    path = Column(String, nullable=False, default='')
    path_in_archive = Column(String, nullable=False, default='')
    info = Column(String, nullable=False, default='')
    fav = Column(Boolean, default=False)
    rating = Column(Integer, nullable=False, default=0)
    times_read = Column(Integer, nullable=False, default=0)
    pub_date = Column(Date)
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.now())
    last_read = Column(DateTime)
    number = Column(Integer, nullable=False, default=0)
    in_archive = Column(Boolean, default=False)
    type_id = Column(Integer, ForeignKey('type.id'))
    language_id = Column(Integer, ForeignKey('language.id'))
    collection_id = Column(Integer, ForeignKey('collection.id'))
    parent_id = Column(Integer, ForeignKey('gallery_namespace.id'))

    exed = Column(Boolean, default=False)
    view = Column(Integer, nullable=False, default=1)

    parent = relationship("GalleryNamespace", back_populates="galleries", cascade="save-update, merge, refresh-expire")
    collection = relationship("Collection", back_populates="galleries", cascade="save-update, merge, refresh-expire")
    urls = relationship("GalleryUrl", back_populates="gallery", cascade="all,delete-orphan")
    language = relationship("Language", back_populates="galleries", cascade="save-update, merge, refresh-expire")
    type = relationship("GalleryType", back_populates="galleries", cascade="save-update, merge, refresh-expire")
    circles = relationship("Circle", secondary=gallery_circles, back_populates='galleries', lazy="dynamic", cascade="save-update, merge, refresh-expire")
    artists = relationship("Artist", secondary=gallery_artists, back_populates='galleries', lazy="joined", cascade="save-update, merge, refresh-expire")
    lists = relationship("List", secondary=gallery_lists, back_populates='galleries', lazy="dynamic")
    pages = relationship("Page", back_populates="gallery", cascade="all,delete-orphan")
    titles = relationship("Title", back_populates="gallery", lazy='joined', cascade="all,delete-orphan")
    tags = relationship("NamespaceTags", secondary=gallery_tags, lazy="dynamic")
    profiles = relationship("Profile", secondary=gallery_profiles, cascade="all")

    @validates("times_read")
    def _add_history(self, key, value):
        sess = object_session(self)
        if sess:
            sess.add(History(self))
        else:
            log_w("Cannot add gallery history because no session exists for this object")
        return value

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.rating = 0
        self.path = ''
        self.in_archive = False

    @property
    def title(self):
        "Returns default title"
        if not hasattr(self, '_title') or not self._title:
            if len(self.titles) == 1:
                self._title = self.titles[0]
            else:
                # TODO: title in default language here
                raise NotImplementedError
        return self._title

    @title.setter
    def title(self, t):
        if hasattr(self, '_title') and self._title:
            self._title.name = t

    @property
    def file_type(self):
        ""
        if not hasattr(self, '_file_type'):
            _, self._file_type = os.path.splitext(self.path)
            if not self._file_type:
                self._file_type = 'folder'
        return self._file_type

    def exists(self):
        "Checks if gallery exists by path"
        #TODO: may want to return the found gallery to inform user
        e = False
        g = self.__class__
        if self.path:
            head, tail = os.path.split(self.path)
            p, ext = os.path.splitext(tail if tail else head)
            sess = constants.db_session()
            if self.in_archive:
                head, tail = os.path.split(self.path_in_archive)
                p_a = tail if tail else head
                e = sess.query(self.__class__.id).filter(and_(g.path.ilike("%{}%".format(p)),
                                                          g.path_in_archive.ilike("%{}%".format(p_a)))).scalar() is not None
            else:
                e = sess.query(self.__class__.id).filter(and_(g.path.ilike("%{}%".format(p)))).scalar() is not None
            sess.close()
        else:
            log_w("Could not query for existence because no path was set.")
        return e

    def _nstag_to_dict(self, namespacetags):
        """
        """
        tags_dict = {}
        for nstag in namespacetags:
            ns_name = nstag.namespace.name
            if not ns_name in tags_dict:
                tags = tags_dict[ns_name] = []
            else:
                tags = tags_dict[ns_name]
            tag_name = nstag.tag.name
            if not tag_name in tags:
                tags.append(tag_name)
        return tags_dict

    def _dict_to_nstag(self, tags_dict):
        """
        """
        nstags = []
        for namespace in tags_dict:
            ns = Namespace()
            ns.name = namespace.capitalize()
            ns = ns.exists(True)

            for t in tags_dict[namespace]:
                tag = Tag()
                tag.name = t
                tag = tag.exists(True)
                
                nstag = NamespaceTags(ns, tag).mapping_exists()
                nstags.append(nstag)
        return nstags


    def string_to_nstags(self, string, ns_capitalize=True):
        "Receives a string of tags and converts it to a dict of tags"
        namespace_tags = {'default':[]}
        level = 0 # so we know if we are in a list
        buffer = ""
        stripped_set = set() # we only need unique values
        for n, x in enumerate(string, 1):

            if x == '[':
                level += 1 # we are now entering a list
            if x == ']':
                level -= 1 # we are now exiting a list


            if x == ',': # if we meet a comma
                # we trim our buffer if we are at top level
                if level is 0:
                    # add to list
                    stripped_set.add(buffer.strip())
                    buffer = ""
                else:
                    buffer += x
            elif n == len(string): # or at end of string
                buffer += x
                # add to list
                stripped_set.add(buffer.strip())
                buffer = ""
            else:
                buffer += x

        def tags_in_list(br_tags):
            "Receives a string of tags enclosed in brackets, returns a list with tags"
            unique_tags = set()
            tags = br_tags.replace('[', '').replace(']','')
            tags = tags.split(',')
            for t in tags:
                if len(t) != 0:
                    unique_tags.add(t.strip().lower())
            return list(unique_tags)

        unique_tags = set()
        for ns_tag in stripped_set:
            splitted_tag = ns_tag.split(':')
            # if there is a namespace
            if len(splitted_tag) > 1 and len(splitted_tag[0]) != 0:
                if splitted_tag[0] != 'default':
                    if ns_capitalize:
                        namespace = splitted_tag[0].capitalize()
                    else:
                        namespace = splitted_tag[0]
                else:
                    namespace = splitted_tag[0]
                tags = splitted_tag[1]
                # if tags are enclosed in brackets
                if '[' in tags and ']' in tags:
                    tags = tags_in_list(tags)
                    tags = [x for x in tags if len(x) != 0]
                    # if namespace is already in our list
                    if namespace in namespace_tags:
                        for t in tags:
                            # if tag not already in ns list
                            if not t in namespace_tags[namespace]:
                                namespace_tags[namespace].append(t)
                    else:
                        # to avoid empty strings
                        namespace_tags[namespace] = tags
                else: # only one tag
                    if len(tags) != 0:
                        if namespace in namespace_tags:
                            namespace_tags[namespace].append(tags)
                        else:
                            namespace_tags[namespace] = [tags]
            else: # no namespace specified
                tag = splitted_tag[0]
                if len(tag) != 0:
                    unique_tags.add(tag.lower())

        if len(unique_tags) != 0:
            for t in unique_tags:
                namespace_tags['default'].append(t)

        return self._dict_to_nstag(namespace_tags)

    def tags_to_string(self, csv=False):
        """
        Takes gallery tags and converts it to string, returns string
        if csv is set to True, returns a CSV string, else a dict-like string
        """
        gallery_tag = self._nstag_to_dict(self.tags.all())

        string = ""
        if not csv:
            for n, namespace in enumerate(sorted(gallery_tag), 1):
                if len(gallery_tag[namespace]) != 0:
                    if namespace != 'default':
                        string += namespace + ":"

                    # find tags
                    if namespace != 'default' and len(gallery_tag[namespace]) > 1:
                        string += '['
                    for x, tag in enumerate(sorted(gallery_tag[namespace]), 1):
                        # if we are at the end of the list
                        if x == len(gallery_tag[namespace]):
                            string += tag
                        else:
                            string += tag + ', '
                    if namespace != 'default' and len(gallery_tag[namespace]) > 1:
                        string += ']'

                    # if we aren't at the end of the list
                    if not n == len(gallery_tag):
                        string += ', '
        else:
            for n, namespace in enumerate(sorted(gallery_tag), 1):
                if len(gallery_tag[namespace]) != 0:
                    if namespace != 'default':
                        string += namespace + ","

                    # find tags
                    for x, tag in enumerate(sorted(gallery_tag[namespace]), 1):
                        # if we are at the end of the list
                        if x == len(gallery_tag[namespace]):
                            string += tag
                        else:
                            string += tag + ', '

                    # if we aren't at the end of the list
                    if not n == len(gallery_tag):
                        string += ', '

        return string

    def __repr__(self):
        return ''
        return """
<Gallery - {}>
Titles: {}
Artists: {}
Path: {}
In Archive: {}
Path In Archive: {}
language: {}
<Gallery END - {}>
""".format(self.id, self.titles, self.artists, self.path, self.in_archive, self.path_in_archive, self.language, self.id)

    def __keyword_search(self, ns, tag, args=[]):
        term = ''
        lt, gt = range(2)
        def _search(term):
            if app_constants.Search.Regex in args:
                if utils.regex_search(tag, term, args):
                    return True
            else:
                if app_constants.DEBUG:
                    print(tag, term)
                if utils.search_term(tag, term, args):
                    return True
            return False

        def _operator_parse(tag):
            o = None
            if tag:
                if tag[0] == '<':
                    o = lt
                    tag = tag[1:]
                elif tag[0] == '>':
                    o = gt
                    tag = tag[1:]
            return tag, o

        def _operator_supported(attr, date=False):
            try:
                o_tag, o = _operator_parse(tag)
                if date:
                    o_tag = dateparser.parse(o_tag, dayfirst=True)
                    if o_tag:
                        o_tag = o_tag.date()
                else:
                    o_tag = int(o_tag)
                if o != None:
                    if o == gt:
                        return o_tag < attr
                    elif o == lt:
                        return o_tag > attr
                else:
                    return o_tag == attr
            except ValueError:
                return False

        if ns == 'Title':
            term = self.title
        elif ns in ['Language', 'Lang']:
            term = self.language
        elif ns == 'Type':
            term = self.type
        elif ns == 'Status':
            term = self.status
        elif ns == 'Artist':
            term = self.artist
        elif ns in ['Descr', 'Description']:
            term = self.info
        elif ns in ['Chapter', 'Chapters']:
            return _operator_supported(self.chapters.count())
        elif ns in ['Read_count', 'Read count', 'Times_read', 'Times read']:
            return _operator_supported(self.times_read)
        elif ns in ['Rating', 'Stars']:
            return _operator_supported(self.rating)
        elif ns in ['Date_added', 'Date added']:
            return _operator_supported(self.date_added.date(), True)
        elif ns in ['Pub_date', 'Publication', 'Pub date']:
            if self.pub_date:
                return _operator_supported(self.pub_date.date(), True)
            return False
        elif ns in ['Last_read', 'Last read']:
            if self.last_read:
                return _operator_supported(self.last_read.date(), True)
            return False
        return _search(term)

    @classmethod
    def _keyword_search(cls, helper, query, attr, tag, custom_filter=None, args=[]):
        if tag in ('none', 'null'):
            helper.add(query.filter(attr.in_((None, ''))).all())
        else:
            try:
                f = custom_filter if custom_filter else attr.ilike("%{}%".format(tag))
                helper.add(query.filter(f).all())
            except exc.InvalidRequestError: # pretty sure it occurs when no such attr is found on a gallery
                pass

    @classmethod
    def search(cls, key, args=[], fav=False, session=None):
        "Check if gallery contains keyword"
        if not session:
            session = constants.db_session()
        if fav:
            q = session.query(cls.id).filter(cls.fav == True)
        else:
            q = session.query(cls.id)
        if key:
            is_exclude = False if key[0] == '-' else True
            key = key[1:] if not is_exclude else key
            helper = utils._ValidContainerHelper()
            # check in title/artist/language
            found = False
            has_namespace = False
            if ':' in key and key[len(key)-1] != ':':
                has_namespace = True

            tags = key.split(':')
            ns = tag = ''
            # only namespace is lowered and capitalized for now
            if len(tags) > 1:
                ns = tags[0].lower().capitalize()
                tag = tags[1]
            else:
                tag = tags[0]

            if not has_namespace:
                for g_attr, attr in [(Gallery.artists, Artist), (Gallery.titles, Title), (Language, Language)]:
                    if app_constants.Search.Regex in args:
                        helper.add(q.join(g_attr).filter(attr.name.ilike(key)).all())
                    else:
                        helper.add(q.join(g_attr).filter(attr.name.ilike("%{}%".format(key))).all())
            else:
                if ns == 'Title':
                    cls._keyword_search(helper, q.join(Gallery.titles), Title.name, tag, args=args)
                elif ns == 'Type':
                    cls._keyword_search(helper, q.join(GalleryType), GalleryType.name, tag, args=args)
                elif ns == 'Status':
                    cls._keyword_search(helper, q.join(Status), Status.name, tag, args=args)
                elif ns == 'Artist':
                    cls._keyword_search(helper, q.join(Gallery.artists), Artist.name, tag, args=args)
                elif ns in ('Language', 'Lang'):
                    cls._keyword_search(helper, q.join(Language), Language.name, tag, args=args)
                elif ns in ('Descr', 'Description'):
                    cls._keyword_search(helper, q, Gallery.info, tag, args=args)
                #elif ns in ('Read_count', 'Read count', 'Times_read', 'Times read'):
                #    cls._keyword_search(helper, q, Gallery.times_read, tag, custom_filter=Gallery.times_read==tag, args=args)
                #elif ns in ('Rating', 'Stars'):
                #    cls._keyword_search(helper, q, Gallery.rating, tag, custom_filter=Gallery.rating==tag, args=args)
                #elif ns in ('Date_added', 'Date added'):
                #    cls._keyword_search(helper, q, Gallery.rating, tag, custom_filter=Gallery.rating==tag, args=args)
                #elif ns in ('Pub_date', 'Publication', 'Pub date'):
                #    cls._keyword_search(helper, q, Gallery.rating, tag, custom_filter=Gallery.rating==tag, args=args)
                #elif ns in ('Last_read', 'Last read'):
                #    pass

            ## check in tag
            #if not found:
            #    tags = key.split(':')
            #    ns = tag = ''
            #    # only namespace is lowered and capitalized for now
            #    if len(tags) > 1:
            #        ns = tags[0].lower().capitalize()
            #        tag = tags[1]
            #    else:
            #        tag = tags[0]

            #    # very special keywords
            #    if ns:
            #        key_word = ['none', 'null']
            #        if ns == 'Tag' and tag in key_word:
            #            if not cls.tags:
            #                return is_exclude
            #        elif ns == 'Artist' and tag in key_word:
            #            if not cls.artist:
            #                return is_exclude
            #        elif ns == 'Status' and tag in key_word:
            #            if not cls.status or cls.status == 'Unknown':
            #                return is_exclude
            #        elif ns == 'Language' and tag in key_word:
            #            if not cls.language:
            #                return is_exclude
            #        elif ns == 'Url' and tag in key_word:
            #            if not cls.link:
            #                return is_exclude
            #        elif ns in ('Descr', 'Description') and tag in key_word:
            #            if not cls.info or cls.info == 'No description..':
            #                return is_exclude
            #        elif ns == 'Type' and tag in key_word:
            #            if not cls.type:
            #                return is_exclude
            #        elif ns in ('Publication', 'Pub_date', 'Pub date') and tag in key_word:
            #            if not cls.pub_date:
            #                return is_exclude
            #        elif ns == 'Path' and tag in key_word:
            #            if cls.dead_link:
            #                return is_exclude

            #    if app_constants.Search.Regex in args:
            #        if ns:
            #            if cls._keyword_search(ns, tag, args = args):
            #                return is_exclude

            #            for x in cls.tags:
            #                if utils.regex_search(ns, x):
            #                    for t in cls.tags[x]:
            #                        if utils.regex_search(tag, t, True, args=args):
            #                            return is_exclude
            #        else:
            #            for x in cls.tags:
            #                for t in cls.tags[x]:
            #                    if utils.regex_search(tag, t, True, args=args):
            #                        return is_exclude
            #    else:
            #        if ns:
            #            if cls._keyword_search(ns, tag, args=args):
            #                return is_exclude

            #            if ns in cls.tags:
            #                for t in cls.tags[ns]:
            #                    if utils.search_term(tag, t, True, args=args):
            #                        return is_exclude
            #        else:
            #            for x in cls.tags:
            #                for t in cls.tags[x]:
            #                    if utils.search_term(tag, t, True, args=args):
            #                        return is_exclude
            #else:
            #    return is_exclude
            return helper.done()
        else:
            ids = q.all()
            return ids if ids else [None]

page_profiles = profile_association("page")

class Page(ProfileMixin, Base):
    __tablename__ = 'page'
    number = Column(Integer, nullable=False, default=0)
    name = Column(String, nullable=False, default='')
    hash_id = Column(Integer, ForeignKey('hash.id'))
    gallery_id = Column(Integer, ForeignKey('gallery.id'), nullable=False)

    hash = relationship("Hash", cascade="save-update, merge, refresh-expire")
    gallery = relationship("Gallery", back_populates="pages")
    profiles = relationship("Profile", secondary=page_profiles, cascade="all")

    def __repr__(self):
        return ''
        return "Page ID:{}\nPage:{}\nProfile:{}\nPageHash:{}".format(self.id, self.number, self.profile, self.hash)

    @property
    def file_type(self):
        ext = ''
        if self.name:
            _, ext = os.path.splitext(self.name)
        return ext.lower()

class Title(Base):
    __tablename__ = 'title'
    name = Column(String, nullable=False, default="")
    language_id = Column(Integer, ForeignKey('language.id'))
    gallery_id = Column(Integer, ForeignKey('gallery.id'), nullable=False)

    language = relationship("Language", cascade="save-update, merge, refresh-expire")
    gallery = relationship("Gallery", lazy='joined', back_populates="titles")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class GalleryUrl(Base):
    __tablename__ = 'gallery_url'
    url = Column(String, nullable=False, default='')
    gallery_id = Column(Integer, ForeignKey('gallery.id'))

    gallery = relationship("Gallery", back_populates="urls")


if __name__ == '__main__':
    Session = sessionmaker()
else:
    Session = scoped_session(sessionmaker())

@event.listens_for(Session, 'after_flush_postexec')
def assign_default_collection(session, f_ctx):
    for g in session.query(Gallery).filter(Gallery.collection == None).all():
        coll = session.query(Collection).filter(Collection.title == "No Collection").scalar()
        if not coll:
            log_e("Could not assign default collection. No such collection exists.")
            return
        g.collection = coll

@event.listens_for(Session, 'before_commit')
def delete_artist_orphans(session):
    session.query(Artist).filter(~Artist.galleries.any()).delete(synchronize_session=False)

@event.listens_for(Session, 'before_commit')
def delete_tag_orphans(session):
    session.query(Tag).filter(~Tag.namespaces.any()).delete(synchronize_session=False)

@event.listens_for(Session, 'before_commit')
def delete_namespace_orphans(session):
    session.query(Namespace).filter(~Namespace.tags.any()).delete(synchronize_session=False)

@event.listens_for(Session, 'before_commit')
def delete_collection_orphans(session):
    session.query(Collection).filter(and_(~Collection.galleries.any(), Collection.title != "No Collection")).delete(synchronize_session=False)

@event.listens_for(Session, 'before_commit')
def delete_namespace_orphans(session):
    session.query(Namespace).filter(~Namespace.tags.any()).delete(synchronize_session=False)

@event.listens_for(Session, 'before_commit')
def delete_namespacetags_orphans(session):
    tagids = [r.id for r in session.query(Tag.id).all()]
    if tagids:
        session.query(NamespaceTags).filter(~NamespaceTags.tag_id.in_(tagids)).delete(synchronize_session=False)
    else:
        session.query(NamespaceTags).delete(synchronize_session=False)

@event.listens_for(Session, 'before_commit')
def delete_circle_orphans(session):
    session.query(Circle).filter(~Circle.galleries.any()).delete(synchronize_session=False)

@event.listens_for(Session, 'before_commit')
def delete_gallery_namespace_orphans(session):
    session.query(GalleryNamespace).filter(~GalleryNamespace.galleries.any()).delete(synchronize_session=False)

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
            "unknown regular expression match operator: %s" % operator,
            would_be_sql_string, None, e)

    # compile the expression as an invocation of the custom function
    regex_func = getattr(func, func_name)
    regex_func_call = regex_func(element.left, element.right)
    return compiler.process(regex_func_call)
    

@event.listens_for(Engine, 'connect')
def sqlite_engine_connect(dbapi_connection, connection_record):
    """Listener for the event of establishing connection to a SQLite database.
    Creates the functions handling regular expression operators
    within SQLite engine, pointing them to their Python implementations above.
    """

    for name, function in SQLITE_REGEX_FUNCTIONS.values():
        dbapi_connection.create_function(name, 2, function)

def init_defaults(sess):
    ""
    coll = sess.query(Collection).filter(Collection.title == "No Collection").scalar()
    if not coll:
       coll = Collection()
       coll.title = "No Collection"
       coll.info = "Galleries not in any collections end up here"
       sess.add(coll)
       sess.commit()

def check_db_version(sess):
    "Checks if DB version is allowed. Raises dialog if not"
    try:
        life = sess.query(Life).one_or_none()
    except exc.NoSuchTableError:
        raise exceptions.DatabaseInitError("Invalid Database")
    if life:
        if life.version not in constants.db_version:
            log_c("Incompatible database version")
            log_d('Local database version: {}\nProgram database version:{}'.format(life.version,
                                                                         constants.db_version))
            return False
    else:
        life = Life()
        sess.add(life)
        life.version = constants.db_version[0]
        life.times_opened = 0
        log_i("Succesfully initiated database")
        log_i("DB Version: {}".format(life.version))

    life.times_opened += 1
    t = life.id
    sess.commit()
    init_defaults(sess)
    return True

def init_db():
    engine = create_engine(os.path.join("sqlite:///", constants.db_path), echo=constants.debug)
    Base.metadata.create_all(engine)
    Session.configure(bind=engine)
    constants.db_session = Session

    return check_db_version(Session())
