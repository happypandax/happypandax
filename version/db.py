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

import db_constants
import app_constants
import utils

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
            sess = db_constants.SESSION()
        sess.delete(self)
        return sess

class NameMixin:
    name = Column(String, nullable=False, default='', unique=True)

    def exists(self, full=False, strict=False):
        "Full: queries for the full object and returns it"
        sess = db_constants.SESSION()
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

    version = Column(Float, nullable=False, default=db_constants.CURRENT_DB_VERSION,)
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
        sess = db_constants.SESSION()
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

    galleries = relationship("Gallery", back_populates="collection", cascade="save-update, merge, refresh-expire", lazy="dynamic")
    profiles = relationship("Profile", secondary=collection_profiles, cascade="all")

    @property
    def rating(self):
        "Calculates average rating from galleries"
        return 5

    @classmethod
    def search(cls, key, args=[], session=None):
        "Check if gallery contains keyword"
        if not session:
            session = db_constants.SESSION()
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
            sess = db_constants.SESSION()
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
            session = db_constants.SESSION()
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
        raise db_constants.DatabaseInitError("Invalid Database")
    if life:
        if life.version not in db_constants.DB_VERSION:
            log_c("Incompatible database version")
            log_d('Local database version: {}\nProgram database version:{}'.format(life.version,
                                                                         db_constants.CURRENT_DB_VERSION))
            return False
    else:
        life = Life()
        sess.add(life)
        life.version = db_constants.CURRENT_DB_VERSION
        life.times_opened = 0
        log_i("Succesfully initiated database")
        log_i("DB Version: {}".format(db_constants.REAL_DB_VERSION))

    db_constants.REAL_DB_VERSION = life.version
    life.times_opened += 1
    t = life.id
    sess.commit()
    init_defaults(sess)
    return True

def init_db():
    engine = create_engine(os.path.join("sqlite:///", db_constants.DB_PATH), echo=app_constants.DEBUG)
    Base.metadata.create_all(engine)
    Session.configure(bind=engine)
    db_constants.SESSION = Session

    return check_db_version(Session())


# unit test
if __name__ == '__main__':
    import unittest, os

    def doublegen(it):
        while it:
            yield (it.pop(), it.pop())

    class GeneralTest(unittest.TestCase):
        def setUp(self):
            if os.path.exists("dbunittest.db"):
                os.remove("dbunittest.db")
            engine = create_engine("sqlite:///dbunittest.db")
            Session.configure(bind=engine)
            Base.metadata.create_all(engine)
            db_constants.SESSION = Session
            self.session = Session()
            self.gallery = Gallery()
            self.session.add(self.gallery)
            self.session.commit()

        def test_exists(self):
            self.gallery.artists.append(Artist(name="lol"))
            self.session.commit()
            self.assertEqual(self.session.query(Artist).count(), 1)

            artist = Artist(name="lol")
            self.assertTrue(artist.exists())
            artist.name = "lol2"
            self.assertFalse(artist.exists())

            p = "hello/here.zip"
            p_a = "gallery"
            self.gallery.path = p
            self.session.commit()
            g = Gallery()
            g.path = p
            self.assertTrue(g.exists())
            g.path = "nope"
            self.assertFalse(g.exists())
            
            self.gallery.path_in_archive = p_a
            self.session.commit()
            g.path = p
            g.path_in_archive = p_a
            g.in_archive = True
            self.assertTrue(g.exists())
            g.path_in_archive = "nope"
            self.assertFalse(g.exists())



        def test_types(self):
            self.gallery.title = ""
            self.gallery.fav = True
            self.gallery.times_read = 2
            self.gallery.pub_date = datetime.date.today()
            self.gallery.timestamp = datetime.datetime.now()
            self.gallery.last_read = datetime.datetime.now()
            self.session.commit()

        def test_history(self):
            self.gallery.times_read += 1
            self.assertEqual(self.session.query(History).count(), 1)
            self.gallery.times_read += 1
            self.session.commit()
            self.assertEqual(self.session.query(History).count(), 2)

            self.gallery.delete()

            self.assertEqual(self.session.query(History).count(), 2)

            self.assertIsNone(self.session.query(History).all()[0].gallery)

        @unittest.expectedFailure
        def test_typesfail(self):
            with self.assertRaises(AssertionError):
                self.gallery.title = 2
            with self.assertRaises(AssertionError):
                self.gallery.fav = 2
            with self.assertRaises(AssertionError):
                self.gallery.fav = ""
            with self.assertRaises(AssertionError):
                self.gallery.last_read = datetime.date.today()
            with self.assertRaises(AssertionError):
                self.gallery.language = 2
            with self.assertRaises(AssertionError):
                self.gallery.rating = ""

        def test_url(self):
            self.gallery.urls.append(GalleryUrl(url="http://www.google.com"))
            self.session.commit()

        def test_page(self):
            page = Page()
            page.number = 1
            self.gallery.pages.append(page)
            self.session.commit()
            self.assertEqual(page.gallery_id, self.gallery.id)
            page.hash = Hash(name="hello")
            self.session.commit()
            self.assertEqual(page.hash.name, "hello")

        def test_pages(self):
            pages = [Page(number=str(x)) for x in range(10)]
            self.gallery.pages.extend(pages)
            self.session.commit()
            self.assertEqual(pages[0].gallery_id, self.gallery.id)

        def test_title(self):
            lang = Language(name="English")
            title = Title()
            title.language = lang
            self.gallery.titles.append(title)
            self.session.commit()
            self.assertEqual(title.gallery_id, self.gallery.id)
            self.assertEqual(self.session.query(Title).count(), 1)
            self.assertEqual(self.session.query(Language).count(), 1)
            #test delete
            title.delete()
            self.assertEqual(self.session.query(Title).count(), 0)
            self.assertEqual(self.session.query(Gallery).count(), 1)
            self.assertEqual(self.session.query(Language).count(), 1)

        def test_titles(self):
            lang = Language(name="English")
            titles = [Title(language=lang) for x in range(10)]
            self.gallery.titles.extend(titles)
            self.session.commit()
            self.assertEqual(titles[0].gallery_id, self.gallery.id)
            self.assertEqual(self.session.query(Title).count(), 10)
            self.assertEqual(self.session.query(Language).count(), 1)
            #test delete
            self.gallery.delete()
            self.assertEqual(self.session.query(Title).count(), 0)
            self.assertEqual(self.session.query(Language).count(), 1)
            self.assertEqual(self.session.query(Gallery).count(), 0)

        def test_tag_and_ns(self):
            for x in range(10):
                tag = Tag()
                tag.name = "tag" + str(x)
                ns = Namespace()
                ns.name = "ns" + str(x)
                nstag = NamespaceTags(ns, tag)
                self.gallery.tags.append(nstag)
            self.session.commit()

            self.assertEqual(self.gallery.tags.count(), 10)

        def test_many_to_many(self):
            artists = [Artist(name="Artist"+str(x)) for x in range(10)]
            circles = [Circle(name="Circle"+str(x)) for x in range(10)]

            self.gallery.artists.extend(artists)
            self.gallery.circles.extend(circles)

            self.session.commit()

            self.assertGreater(len(self.gallery.artists), 0)
            self.assertGreater(self.gallery.circles.count(), 0)
            self.assertTrue(artists[0].galleries[0].id == self.gallery.id)

        def tearDown(self):
            self.session.close()
            if os.path.exists("dbunittest.db"):
                os.remove("dbunittest.db")

    class CollectionRelationship(unittest.TestCase):
        def setUp(self):
            if os.path.exists("dbcollectionunittest.db"):
                os.remove("dbcollectionunittest.db")
            engine = create_engine("sqlite:///dbcollectionunittest.db")
            Session.configure(bind=engine)
            Base.metadata.create_all(engine)

            self.session = Session()

            self.collections = [Collection(title="col"+str(x)) for x in range(2)]
            self.galleries = [Gallery() for x in range(10)]
            self.session.add_all(self.galleries)
            self.collections[0].galleries.extend(self.galleries[:5])
            self.collections[1].galleries.extend(self.galleries[5:])
            self.session.commit()

            self.assertEqual(self.session.query(Gallery).count(), 10)
            self.assertEqual(self.session.query(Collection).count(), 2)

        def default(self):
            init_defaults(self.session)
            self.assertIsNotNone(self.session.query(Collection).filter(Collection.title == "No Collection").scalar())

            self.session.delete(self.collections[0])
            self.session.delete(self.collections[1])
            self.session.commit()
            self.assertEqual(self.session.query(Collection).count(), 1)
            for g in self.galleries:
                self.assertIsNotNone(g.collection)
                self.assertTrue(g.collection.title == "No Collection")


        def test_delete(self):
            self.session.delete(self.collections[0])
            self.session.commit()
            self.assertEqual(self.session.query(Gallery).count(), 10)
            self.assertEqual(self.session.query(Collection).count(), 1)

        def test_delete2(self):
            self.session.delete(self.galleries[0])
            self.session.commit()
            self.assertEqual(self.session.query(Gallery).count(), 9)
            self.assertEqual(self.session.query(Collection).count(), 2)
            self.assertEqual(self.collections[0].galleries.count(), 4)

        def test_delete3(self):
            for c in self.collections:
                self.session.delete(c)
            self.session.commit()
            self.assertEqual(self.session.query(Gallery).count(), 10)
            self.assertEqual(self.session.query(Collection).count(), 0)

        def test_no_orphans(self):
            self.session.query(Gallery).delete()
            self.session.commit()
            self.assertEqual(self.session.query(Gallery).count(), 0)
            self.assertEqual(self.session.query(Collection).count(), 0)

        def tearDown(self):
            self.session.close()
            if os.path.exists("dbcollectionunittest.db"):
                os.remove("dbcollectionunittest.db")

    class ListRelationship(unittest.TestCase):
        def setUp(self):
            if os.path.exists("dblistunittest.db"):
                os.remove("dblistunittest.db")
            engine = create_engine("sqlite:///dblistunittest.db")
            Session.configure(bind=engine)
            Base.metadata.create_all(engine)

            self.session = Session()

            self.glists = [List(name="list"+str(x)) for x in range(2)]
            self.galleries = [Gallery() for x in range(10)]
            self.session.add_all(self.galleries)
            for gl in self.glists:
                gl.galleries.extend(self.galleries)
            self.session.commit()

        def test_delete(self):
            self.session.delete(self.glists[0])
            self.session.commit()
            self.assertEqual(self.session.query(Gallery).count(), 10)
            self.assertEqual(self.session.query(List).count(), 1)

        def test_delete2(self):
            self.session.delete(self.galleries[0])
            self.session.commit()
            self.assertEqual(self.session.query(Gallery).count(), 9)
            self.assertEqual(self.session.query(List).count(), 2)
            self.assertEqual(self.glists[0].galleries.count(), 9)

        def test_no_orphans(self):
            self.session.query(Gallery).delete()
            self.session.commit()
            self.assertEqual(self.session.query(Gallery).count(), 0)
            self.assertEqual(self.session.query(List).count(), 2)
            self.assertEqual(self.glists[0].galleries.count(), 0)

        def test_no_orphans2(self):
            self.session.query(List).delete()
            self.session.commit()
            self.assertEqual(self.session.query(Gallery).count(), 10)
            self.assertEqual(self.session.query(List).count(), 0)

        def tearDown(self):
            self.session.close()
            if os.path.exists("dblistunittest.db"):
                os.remove("dblistunittest.db")

    class ArtistRelationship(unittest.TestCase):
        def setUp(self):
            if os.path.exists("dbartistunittest.db"):
                os.remove("dbartistunittest.db")
            engine = create_engine("sqlite:///dbartistunittest.db")
            Session.configure(bind=engine)
            Base.metadata.create_all(engine)

            self.session = Session()

            self.artist = Artist()
            self.artist.name = "Artist1"
            self.galleries = [Gallery() for x in range(10)]
            self.session.add_all(self.galleries)
            self.artist.galleries.extend(self.galleries)
            self.session.commit()

            self.assertEqual(self.artist.id, self.galleries[0].artists[0].id)

        def test_delete(self):
            self.session.delete(self.artist)
            self.session.commit()
            self.assertEqual(self.session.query(Gallery).count(), 10)
            self.assertEqual(self.session.query(Artist).count(), 0)

        def test_delete2(self):
            self.session.delete(self.galleries[0])
            self.session.commit()
            self.assertEqual(self.session.query(Gallery).count(), 9)
            self.assertEqual(self.session.query(Artist).count(), 1)

        def test_no_orphans(self):
            self.session.query(Gallery).delete()
            self.session.commit()
            self.assertEqual(self.session.query(Gallery).count(), 0)
            self.assertEqual(self.session.query(Artist).count(), 0)

        def tearDown(self):
            self.session.close()
            if os.path.exists("dbartistunittest.db"):
                os.remove("dbartistunittest.db")

    class CircleRelationship(unittest.TestCase):
        def setUp(self):
            if os.path.exists("dbcircleunittest.db"):
                os.remove("dbcircleunittest.db")
            engine = create_engine("sqlite:///dbcircleunittest.db")
            Session.configure(bind=engine)
            Base.metadata.create_all(engine)

            self.session = Session()

            self.artist = Circle()
            self.artist.name = "Artist1"
            self.galleries = [Gallery() for x in range(10)]
            self.session.add_all(self.galleries)
            self.artist.galleries.extend(self.galleries)
            self.session.commit()

            self.assertEqual(self.artist.id, self.galleries[0].circles[0].id)


        def test_delete(self):
            self.session.delete(self.artist)
            self.session.commit()
            self.assertEqual(self.session.query(Gallery).count(), 10)
            self.assertEqual(self.session.query(Circle).count(), 0)

        def test_delete2(self):
            self.session.delete(self.galleries[0])
            self.session.commit()
            self.assertEqual(self.session.query(Gallery).count(), 9)
            self.assertEqual(self.session.query(Circle).count(), 1)

        def test_no_orphans(self):
            self.session.query(Gallery).delete()
            self.session.commit()
            self.assertEqual(self.session.query(Gallery).count(), 0)
            self.assertEqual(self.session.query(Circle).count(), 0)

        def tearDown(self):
            self.session.close()
            if os.path.exists("dbcircleunittest.db"):
                os.remove("dbcircleunittest.db")


    class HashRelationship(unittest.TestCase):
        def setUp(self):
            if os.path.exists("dbhashunittest.db"):
                os.remove("dbhashunittest.db")
            engine = create_engine("sqlite:///dbhashunittest.db")
            Session.configure(bind=engine)
            Base.metadata.create_all(engine)

            self.session = Session()
            self.gallery = Gallery()
            self.session.add(self.gallery)
            self.session.commit()

            self.hash = Hash()
            self.hash.name = "Hash1"
            self.pages = [Page(number=x) for x in range(10)]
            self.gallery.pages.extend(self.pages)
            self.session.commit()

            self.assertEqual(self.gallery.id, self.pages[0].gallery_id)

            for p in self.pages:
                p.hash = self.hash

            self.session.commit()

            self.assertEqual(self.hash.id, self.pages[0].hash_id)

        def test_delete(self):
            self.session.delete(self.pages[0])
            self.session.commit()

            self.assertEqual(self.session.query(Page).count(), 9)
            self.assertEqual(self.session.query(Hash).count(), 1)

        def test_delete2(self):
            self.session.delete(self.hash)
            self.session.commit()

            self.assertEqual(self.session.query(Page).count(), 10)
            self.assertEqual(self.session.query(Hash).count(), 0)
            self.assertTrue(self.pages[0].hash == None)

        def test_no_orphans(self):
            self.session.query(Page).delete()
            self.session.commit()

            self.assertEqual(self.session.query(Page).count(), 0)
            self.assertEqual(self.session.query(Hash).count(), 1)

        def tearDown(self):
            self.session.close()
            if os.path.exists("dbhashunittest.db"):
                os.remove("dbhashunittest.db")

    class GalleryNSRelationship(unittest.TestCase):
        def setUp(self):
            if os.path.exists("dbgallerynsunittest.db"):
                os.remove("dbgallerynsunittest.db")
            engine = create_engine("sqlite:///dbgallerynsunittest.db")
            Session.configure(bind=engine)
            Base.metadata.create_all(engine)

            self.session = Session()
            self.galleryns = [GalleryNamespace(name="gns"+str(x)) for x in range(2)]
            self.galleries = [Gallery() for x in range(10)]
            self.galleryns[0].galleries.extend(self.galleries[:5])
            self.galleryns[1].galleries.extend(self.galleries[5:])
            self.session.add_all(self.galleryns)
            self.session.commit()

            self.assertEqual(self.session.query(GalleryNamespace).count(), 2)
            self.assertEqual(self.session.query(Gallery).count(), 10)
            self.assertEqual(self.galleries[0].parent_id, self.galleryns[0].id)

        def test_delete(self):
            self.session.delete(self.galleryns[0])
            self.session.commit()

            self.assertEqual(self.session.query(GalleryNamespace).count(), 1)
            self.assertEqual(self.session.query(Gallery).count(), 5)

        def test_delete2(self):
            self.session.delete(self.galleries[0])
            self.session.commit()

            self.assertEqual(self.session.query(GalleryNamespace).count(), 2)
            self.assertEqual(self.session.query(Gallery).count(), 9)

        def test_no_orphans(self):
            self.session.query(Gallery).delete()
            self.session.commit()

            self.assertEqual(self.session.query(GalleryNamespace).count(), 0)
            self.assertEqual(self.session.query(Gallery).count(), 0)

        def test_change_ns(self):
            self.galleryns[1].galleries.append(self.galleries[0])
            self.session.commit()

            self.assertEqual(self.session.query(GalleryNamespace).count(), 2)
            self.assertEqual(self.session.query(Gallery).count(), 10)
            self.assertEqual(self.galleryns[1].galleries.count(), 6)
            self.assertEqual(self.galleryns[0].galleries.count(), 4)

        def tearDown(self):
            self.session.close()
            if os.path.exists("dbgallerynsunittest.db"):
                os.remove("dbgallerynsunittest.db")

    class LanguageRelationship(unittest.TestCase):
        def setUp(self):
            if os.path.exists("dblangunittest.db"):
                os.remove("dblangunittest.db")
            engine = create_engine("sqlite:///dblangunittest.db")
            Session.configure(bind=engine)
            Base.metadata.create_all(engine)

            self.session = Session()

            self.lang = Language()
            self.lang.name = "Con1"
            self.galleries = [Gallery() for x in range(10)]
            self.lang.galleries.extend(self.galleries)
            self.session.add(self.lang)
            self.session.commit()
            self.assertEqual(self.session.query(Language).count(), 1)
            self.assertEqual(self.lang.id, self.galleries[0].language_id)

        def test_delete(self):
            self.session.query(Language).delete()
            self.session.commit()

            self.assertIsNone(self.galleries[0].language)
            self.assertEqual(self.session.query(Gallery).count(), 10)
            self.assertEqual(self.session.query(Language).count(), 0)

        def test_delete2(self):
            self.session.delete(self.galleries[0])
            self.session.commit()

            self.assertEqual(self.session.query(Gallery).count(), 9)
            self.assertEqual(self.session.query(Language).count(), 1)

        def test_orphans(self):
            self.session.query(Gallery).delete()
            self.session.commit()

            self.assertEqual(self.session.query(Gallery).count(), 0)
            self.assertEqual(self.session.query(Language).count(), 1)

        def tearDown(self):
            self.session.close()
            if os.path.exists("dblangunittest.db"):
                os.remove("dblangunittest.db")

    class TypeRelationship(unittest.TestCase):
        def setUp(self):
            if os.path.exists("dbtypeunittest.db"):
                os.remove("dbtypeunittest.db")
            engine = create_engine("sqlite:///dbtypeunittest.db")
            Session.configure(bind=engine)
            Base.metadata.create_all(engine)

            self.session = Session()

            self.type = GalleryType()
            self.type.name = "Con1"
            self.galleries = [Gallery() for x in range(10)]
            self.type.galleries.extend(self.galleries)
            self.session.add(self.type)
            self.session.commit()
            self.assertEqual(self.session.query(GalleryType).count(), 1)
            self.assertEqual(self.type.id, self.galleries[0].type_id)

        def test_delete(self):
            self.session.query(GalleryType).delete()
            self.session.commit()

            self.assertIsNone(self.galleries[0].type)
            self.assertEqual(self.session.query(Gallery).count(), 10)
            self.assertEqual(self.session.query(GalleryType).count(), 0)

        def test_delete2(self):
            self.session.delete(self.galleries[0])
            self.session.commit()

            self.assertEqual(self.session.query(Gallery).count(), 9)
            self.assertEqual(self.session.query(GalleryType).count(), 1)

        def test_orphans(self):
            self.session.query(Gallery).delete()
            self.session.commit()

            self.assertEqual(self.session.query(Gallery).count(), 0)
            self.assertEqual(self.session.query(GalleryType).count(), 1)

        def tearDown(self):
            self.session.close()
            if os.path.exists("dbtypeunittest.db"):
                os.remove("dbtypeunittest.db")

    class StatusRelationship(unittest.TestCase):
        def setUp(self):
            if os.path.exists("dbstatusunittest.db"):
                os.remove("dbstatusunittest.db")
            engine = create_engine("sqlite:///dbstatusunittest.db")
            Session.configure(bind=engine)
            Base.metadata.create_all(engine)

            self.session = Session()

            self.status = Status()
            self.status.name = "Stat1"
            self.galleryns = [GalleryNamespace(name="gns"+str(x)) for x in range(2)]
            self.galleries = [Gallery() for x in range(10)]
            self.galleryns[0].galleries.extend(self.galleries[:5])
            self.galleryns[1].galleries.extend(self.galleries[5:])
            for gns in self.galleryns:
                gns.status = self.status
            self.session.add_all(self.galleryns)
            self.session.add(self.status)
            self.session.commit()
            self.assertEqual(self.session.query(Status).count(), 1)
            self.assertEqual(self.session.query(GalleryNamespace).count(), 2)
            self.assertEqual(self.session.query(Gallery).count(), 10)
            self.assertEqual(self.status, self.galleryns[0].status)

        def test_delete(self):
            self.session.query(Status).delete()
            self.session.commit()

            self.assertIsNone(self.galleryns[0].status)
            self.assertEqual(self.session.query(GalleryNamespace).count(), 2)
            self.assertEqual(self.session.query(Status).count(), 0)

        def test_delete2(self):
            self.session.delete(self.galleryns[0])
            self.session.commit()

            self.assertEqual(self.session.query(GalleryNamespace).count(), 1)
            self.assertEqual(self.session.query(Status).count(), 1)

        def test_orphans(self):
            self.session.query(GalleryNamespace).delete()
            self.session.commit()

            self.assertEqual(self.session.query(GalleryNamespace).count(), 0)
            self.assertEqual(self.session.query(Status).count(), 1)

        def tearDown(self):
            self.session.close()
            if os.path.exists("dbstatusunittest.db"):
                os.remove("dbstatusunittest.db")

    class UrlRelationship(unittest.TestCase):
        def setUp(self):
            if os.path.exists("dburlunittest.db"):
                os.remove("dburlunittest.db")
            engine = create_engine("sqlite:///dburlunittest.db")
            Session.configure(bind=engine)
            Base.metadata.create_all(engine)

            self.session = Session()
            self.gallery = Gallery()
            self.session.add(self.gallery)
            self.session.commit()

            self.urls = [GalleryUrl(url="http://google.com") for x in range(10)]
            self.gallery.urls.extend(self.urls)
            self.session.commit()

            self.assertEqual(self.gallery.id, self.urls[0].gallery_id)
            self.assertEqual(self.session.query(GalleryUrl).count(), 10)

        def test_delete(self):
            self.session.delete(self.urls[0])
            self.session.commit()

            self.assertEqual(self.session.query(GalleryUrl).count(), 9)
            self.assertEqual(self.session.query(Gallery).count(), 1)

        def test_no_orphans(self):
            self.session.delete(self.gallery)
            self.session.commit()

            self.assertEqual(self.session.query(GalleryUrl).count(), 0)
            self.assertEqual(self.session.query(Gallery).count(), 0)

        def tearDown(self):
            self.session.close()
            if os.path.exists("dburlunittest.db"):
                os.remove("dburlunittest.db")

    class TagRelationship(unittest.TestCase):
        def setUp(self):
            if os.path.exists("dbtagunittest.db"):
                os.remove("dbtagunittest.db")
            engine = create_engine("sqlite:///dbtagunittest.db")
            Session.configure(bind=engine)
            Base.metadata.create_all(engine)

            self.session = Session()

            self.namespaces = [Namespace(name="ns"+str(x)) for x in range(20)]
            self.tags = [Tag(name="tag"+str(x)) for x in range(10)]
            self.galleries = [Gallery() for x in range(5)]
            self.session.add_all(self.galleries)
            self.nstags = []
            nsgen = doublegen(self.namespaces)
            for x, tag in enumerate(self.tags):
                doublens = next(nsgen)
                self.nstags.append(NamespaceTags(doublens[0], tag))
                self.nstags.append(NamespaceTags(doublens[1], tag))

            for x, ch in enumerate(self.galleries):
                ch.tags.extend(self.nstags)
            self.session.commit()

            self.assertEqual(self.session.query(Gallery).count(), 5)
            self.assertEqual(self.session.query(Tag).count(), 10)
            self.assertEqual(self.session.query(Namespace).count(), 20)
            self.assertEqual(self.session.query(NamespaceTags).count(), 20)

        def test_delete(self):
            self.session.delete(self.tags[0])
            self.session.commit()
            self.assertEqual(self.session.query(Tag).count(), 9)
            self.assertTrue(self.session.query(Namespace).count() != 0)

        def test_delete2(self):
            self.session.delete(self.tags[0].namespaces[0])
            self.session.commit()
            self.assertEqual(self.session.query(Tag).count(), 10)
            self.assertEqual(self.session.query(Namespace).count(), 19)

        def test_delete3(self):
            self.session.delete(self.galleries[0])
            self.session.commit()
            self.assertEqual(self.session.query(Gallery).count(), 4)
            self.assertTrue(self.session.query(NamespaceTags).count() != 0)
            self.assertTrue(self.session.query(Tag).count() != 0)
            self.assertTrue(self.session.query(Namespace).count() != 0)

        def test_no_orphans(self):
            self.session.query(Gallery).delete()
            self.session.commit()
            self.assertEqual(self.session.query(Gallery).count(), 0)

            self.session.query(Namespace).delete()
            self.session.commit()
            self.assertEqual(self.session.query(Tag).count(), 0)
            self.assertEqual(self.session.query(Namespace).count(), 0)
            self.assertEqual(self.session.query(NamespaceTags).count(), 0)

        def tearDown(self):
            self.session.close()
            if os.path.exists("dbtagunittest.db"):
                os.remove("dbtagunittest.db")


    class ProfileRelationship(unittest.TestCase):
        def setUp(self):
            if os.path.exists("dbprofileunittest.db"):
                os.remove("dbprofileunittest.db")
            engine = create_engine("sqlite:///dbprofileunittest.db")
            Session.configure(bind=engine)
            Base.metadata.create_all(engine)

            self.session = Session()

            self.lists = [List(name="list"+str(x)) for x in range(5)]
            self.gns = [GalleryNamespace(name="gns"+str(x)) for x in range(5)]
            self.galleries = [Gallery() for x in range(5)]
            self.collections = [Collection(title="title"+str(x)) for x in range(5)]
            self.pages = [Page(number=x) for x in range(5)]

            for n, x in enumerate(self.galleries):
                self.collections[n].galleries.append(x)
                self.pages[n].gallery = x
                self.gns[n].galleries.append(x)

            self.session.add_all(self.galleries)
            self.session.add_all(self.lists)
            self.session.commit()

            self.assertEqual(self.session.query(Gallery).count(), 5)
            self.assertEqual(self.session.query(GalleryNamespace).count(), 5)
            self.assertEqual(self.session.query(Collection).count(), 5)
            self.assertEqual(self.session.query(Page).count(), 5)
            self.assertEqual(self.session.query(List).count(), 5)

            self.profiles = [Profile(path="p"+str(x), type=x) for x in range(5)]

            for x in (self.lists, self.gns, self.galleries, self.collections, self.pages):
                for y in x:
                    y.profiles.append(self.profiles[random.randint(0, 4)])

            self.session.commit()

            self.assertEqual(self.session.query(Profile).count(), 5)


        def test_delete(self):
            self.session.delete(self.profiles[0])
            self.session.commit()
            self.assertEqual(self.session.query(Gallery).count(), 5)
            self.assertEqual(self.session.query(GalleryNamespace).count(), 5)
            self.assertEqual(self.session.query(Collection).count(), 5)
            self.assertEqual(self.session.query(Page).count(), 5)
            self.assertEqual(self.session.query(List).count(), 5)
            self.assertEqual(self.session.query(Profile).count(), 4)

        def test_delete2(self):
            self.session.delete(self.pages[0])
            self.session.commit()
            self.assertEqual(self.session.query(Gallery).count(), 5)
            self.assertEqual(self.session.query(GalleryNamespace).count(), 5)
            self.assertEqual(self.session.query(Collection).count(), 5)
            self.assertEqual(self.session.query(Page).count(), 4)
            self.assertEqual(self.session.query(List).count(), 5)
            self.assertEqual(self.session.query(Profile).count(), 4)

        def test_no_orphans(self):
            for x in (self.lists, self.gns):
                for y in x:
                    self.session.delete(y)
            self.session.commit()

            self.assertEqual(self.session.query(Gallery).count(), 0)
            self.assertEqual(self.session.query(GalleryNamespace).count(), 0)
            self.assertEqual(self.session.query(Collection).count(), 0)
            self.assertEqual(self.session.query(Page).count(), 0)
            self.assertEqual(self.session.query(List).count(), 0)
            self.assertEqual(self.session.query(Profile).count(), 0)

        def tearDown(self):
            self.session.close()
            if os.path.exists("dbprofileunittest.db"):
                os.remove("dbprofileunittest.db")

    unittest.main(verbosity=2)