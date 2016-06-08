from sqlalchemy.orm import sessionmaker, relationship, backref, object_session
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (create_engine, event, and_, or_, Boolean, Column, Integer, String, ForeignKey,
                        Table, Date, DateTime, UniqueConstraint)
from sqlalchemy_utils.functions import dependent_objects

import datetime

Base = declarative_base()

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

class Hash(Base):
    __tablename__ = 'hash'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    def __repr__(self):
        return "Hash ID:{}\nHash:{}".format(self.id, self.name)

class NamespaceTags(Base):
    __tablename__ = 'namespace_tags'

    id = Column(Integer, primary_key=True)
    tag_id = Column(Integer, ForeignKey('tag.id'))
    namespace_id = Column(Integer, ForeignKey('namespace.id'))
    __table_args__ = (UniqueConstraint('tag_id', 'namespace_id'),)

    tag = relationship("Tag", cascade="save-update, merge, refresh-expire")
    namespace = relationship("Namespace", cascade="save-update, merge, refresh-expire")

    def __init__(self, ns, tag):
        self.namespace = ns
        self.tag = tag

class Tag(Base):
    __tablename__ = 'tag'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    namespaces = relationship("Namespace", secondary='namespace_tags', back_populates='tags', lazy="dynamic")

    def __repr__(self):
        return "ID:{} -Tag:{}".format(self.id, self.name)

class Namespace(Base):
    __tablename__ = 'namespace'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    tags = relationship("Tag", secondary='namespace_tags', back_populates='namespaces', lazy="dynamic")

    def __repr__(self):
        return "ID:{} - nNamespace:{}".format(self.id, self.name)

gallery_artists = Table('gallery_artists', Base.metadata,
                        Column('artist_id', Integer, ForeignKey('artist.id')),
                        Column('gallery_id', Integer, ForeignKey('gallery.id')),
                        UniqueConstraint('artist_id', 'gallery_id'))


class Artist(Base):
    __tablename__ = 'artist'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, default='', unique=True)

    galleries = relationship("Gallery", secondary=gallery_artists, back_populates='artists', lazy="dynamic")

gallery_circles = Table('gallery_circles', Base.metadata,
                        Column('circle_id', Integer, ForeignKey('circle.id',)),
                        Column('gallery_id', Integer, ForeignKey('gallery.id',)),
                        UniqueConstraint('circle_id', 'gallery_id'))

class Circle(Base):
    __tablename__ = 'circle'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, default='', unique=True)

    galleries = relationship("Gallery", secondary=gallery_circles, back_populates='circles', lazy="dynamic")

gallery_lists = Table('gallery_lists', Base.metadata,
                        Column('list_id', Integer, ForeignKey('list.id')),
                        Column('gallery_id', Integer, ForeignKey('gallery.id')),
                        UniqueConstraint('list_id', 'gallery_id'))

class List(Base):
    __tablename__ = 'list'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, default='')
    filter = Column(String, nullable=False, default='')
    profile = Column(String, nullable=False, default='')
    enforce = Column(Boolean, nullable=False, default=False)
    regex = Column(Boolean, nullable=False, default=False)
    l_case = Column(Boolean, nullable=False, default=False)
    strict = Column(Boolean, nullable=False, default=False)

    galleries = relationship("Gallery", secondary=gallery_lists, back_populates='lists', lazy="dynamic")

class GalleryNamespace(Base):
    __tablename__ = 'gallery_namespace'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    galleries = relationship("Gallery", back_populates="namespace")

    def __repr__(self):
        return "ID:{} - G-Namespace:{}".format(self.id, self.name)

class Convention(Base):
    __tablename__ = 'convention'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)

    galleries = relationship("Gallery", back_populates='convention')

    def __repr__(self):
        return "ID:{} - Convention:{}".format(self.id, self.name)

class Gallery(Base):
    __tablename__ = 'gallery'
    id = Column(Integer, primary_key=True)
    path = Column(String, nullable=False, default='')
    title = Column(String, nullable=False, default='')
    info = Column(String, nullable=False, default='')
    fav = Column(Boolean, default=False)
    type = Column(String, nullable=False, default='')
    language = Column(String, nullable=False, default='')
    rating = Column(Integer, nullable=False, default=0)
    times_read = Column(Integer, nullable=False, default=0)
    status = Column(String, nullable=False, default='')
    pub_date = Column(Date)
    timestamp = Column(DateTime, nullable=False, default=datetime.datetime.now())
    last_read = Column(DateTime)
    convention_id = Column(Integer, ForeignKey('convention.id'))
    namespace_id = Column(Integer, ForeignKey('gallery_namespace.id'))

    exed = Column(Boolean, default=False)
    view = Column(Integer, nullable=False, default=1)

    urls = relationship("GalleryUrl", back_populates="gallery", cascade="all,delete-orphan")
    chapters = relationship("Chapter", back_populates="gallery", cascade="all", lazy="dynamic")
    convention = relationship("Convention", back_populates="galleries", cascade="save-update, merge, refresh-expire")
    namespace = relationship("GalleryNamespace", back_populates="galleries", cascade="save-update, merge, refresh-expire")
    circles = relationship("Circle", secondary=gallery_circles, back_populates='galleries', lazy="dynamic", cascade="save-update, merge, refresh-expire")
    artists = relationship("Artist", secondary=gallery_artists, back_populates='galleries', lazy="dynamic", cascade="save-update, merge, refresh-expire")
    lists = relationship("List", secondary=gallery_lists, back_populates='galleries', lazy="dynamic")

chapter_tags = Table('chapter_tags', Base.metadata,
                        Column('namespace_tag_id', Integer, ForeignKey('namespace_tags.id')),
                        Column('chapter_id', Integer, ForeignKey('chapter.id')),
                        UniqueConstraint('namespace_tag_id', 'chapter_id'))

class Chapter(Base):
    __tablename__ = 'chapter'
    id = Column(Integer, primary_key=True)
    gallery_id = Column(Integer, ForeignKey('gallery.id', ondelete="cascade"), nullable=False)
    title = Column(String, nullable=False, default='')
    path = Column(String, nullable=False, default='')
    number = Column(Integer, nullable=False, default=0)
    in_archive = Column(Boolean, default=False)

    gallery = relationship("Gallery", back_populates="chapters")
    pages = relationship("Page", back_populates="chapter", cascade="all,delete-orphan")
    tags = relationship("NamespaceTags", secondary=chapter_tags, lazy="dynamic")

class Page(Base):
    __tablename__ = 'page'
    id = Column(Integer, primary_key=True)
    profile = Column(String)
    number = Column(Integer)
    hash_id = Column(Integer, ForeignKey('hash.id'))
    chapter_id = Column(Integer, ForeignKey('chapter.id'), nullable=False)

    hash = relationship("Hash", cascade="save-update, merge, refresh-expire")
    chapter = relationship("Chapter", back_populates="pages")

    def __repr__(self):
        return "Page ID:{}\nPage:{}\nProfile:{}\nPageHash:{}".format(self.id, self.number, self.profile, self.hash)

class GalleryUrl(Base):
    __tablename__ = 'gallery_url'
    id = Column(Integer, primary_key=True)
    url = Column(String, nullable=False, default='')
    gallery_id = Column(Integer, ForeignKey('gallery.id'))

    gallery = relationship("Gallery", back_populates="urls")


engine = create_engine("sqlite:///dbtest.db")
Session = sessionmaker(bind=engine)

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
def delete_convention_orphans(session):
    session.query(Convention).filter(~Convention.galleries.any()).delete(synchronize_session=False)

@event.listens_for(Session, 'before_commit')
def delete_gallery_namespace_orphans(session):
    session.query(GalleryNamespace).filter(~GalleryNamespace.galleries.any()).delete(synchronize_session=False)

#@event.listens_for(Engine, "connect")
#def set_sqlite_pragma(dbapi_connection, connection_record):
#    cursor = dbapi_connection.cursor()
#    cursor.execute("PRAGMA foreign_keys=ON")
#    cursor.close()

Base.metadata.create_all(engine)


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

            self.session = Session()
            self.gallery = Gallery()
            self.session.add(self.gallery)
            self.chapter = Chapter()
            self.gallery.chapters.append(self.chapter)
            self.session.commit()

        def test_types(self):
            self.gallery.title = ""
            self.gallery.fav = True
            self.gallery.times_read = 2
            self.gallery.pub_date = datetime.date.today()
            self.gallery.timestamp = datetime.datetime.now()
            self.gallery.last_read = datetime.datetime.now()
            self.session.commit()


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
            self.chapter.pages.append(page)
            self.session.commit()
            self.assertEqual(page.chapter_id, self.chapter.id)
            page.hash = Hash(name="hello")
            self.session.commit()
            self.assertEqual(page.hash.name, "hello")

        def test_pages(self):
            pages = [Page(number=str(x)) for x in range(10)]
            self.chapter.pages.extend(pages)
            self.session.commit()
            self.assertEqual(pages[0].chapter_id, self.chapter.id)

        def test_tag_and_ns(self):
            for x in range(10):
                tag = Tag()
                tag.name = "tag" + str(x)
                ns = Namespace()
                ns.name = "ns" + str(x)
                nstag = NamespaceTags(ns, tag)
                self.chapter.tags.append(nstag)
            self.session.commit()

            self.assertEqual(self.chapter.tags.count(), 10)

        def test_many_to_many(self):
            artists = [Artist(name="Artist"+str(x)) for x in range(10)]
            circles = [Circle(name="Circle"+str(x)) for x in range(10)]

            self.gallery.artists.extend(artists)
            self.gallery.circles.extend(circles)

            self.session.commit()

            self.assertGreater(self.gallery.artists.count(), 0)
            self.assertGreater(self.gallery.circles.count(), 0)
            self.assertTrue(artists[0].galleries[0].id == self.gallery.id)

        def tearDown(self):
            self.session.close()
            if os.path.exists("dbunittest.db"):
                os.remove("dbunittest.db")

    class ListRelationship(unittest.TestCase):
        def setUp(self):
            if os.path.exists("dblistunittest.db"):
                os.remove("dblistunittest.db")
            engine = create_engine("sqlite:///dblistunittest.db")
            Session.configure(bind=engine)
            Base.metadata.create_all(engine)

            self.session = Session()

            self.glists = [List(name="list"+str(x)) for x in range(2)]
            self.galleries = [Gallery(title="title"+str(x)) for x in range(10)]
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
            self.galleries = [Gallery(title="title"+str(x)) for x in range(10)]
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
            self.galleries = [Gallery(title="title"+str(x)) for x in range(10)]
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
            self.chapter = Chapter()
            self.gallery.chapters.append(self.chapter)
            self.session.commit()

            self.hash = Hash()
            self.hash.name = "Hash1"
            self.pages = [Page(number=x) for x in range(10)]
            self.chapter.pages.extend(self.pages)
            self.session.commit()

            self.assertEqual(self.chapter.id, self.pages[0].chapter_id)

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
            self.galleryns = GalleryNamespace(name="gns 1")
            self.galleries = [Gallery(title="title"+str(x)) for x in range(10)]
            self.galleryns.galleries.extend(self.galleries)
            self.session.add(self.galleryns)
            self.session.commit()

            self.assertEqual(self.session.query(GalleryNamespace).count(), 1)
            self.assertEqual(self.session.query(Gallery).count(), 10)
            self.assertEqual(self.galleries[0].namespace_id, self.galleryns.id)

        def test_delete(self):
            self.session.delete(self.galleryns)
            self.session.commit()

            self.assertEqual(self.session.query(GalleryNamespace).count(), 0)
            self.assertEqual(self.session.query(Gallery).count(), 10)

        def test_delete2(self):
            self.session.delete(self.galleries[0])
            self.session.commit()

            self.assertEqual(self.session.query(GalleryNamespace).count(), 1)
            self.assertEqual(self.session.query(Gallery).count(), 9)

        def test_no_orphans(self):
            self.session.query(Gallery).delete()
            self.session.commit()

            self.assertEqual(self.session.query(GalleryNamespace).count(), 0)
            self.assertEqual(self.session.query(Gallery).count(), 0)

        def tearDown(self):
            self.session.close()
            if os.path.exists("dbgallerynsunittest.db"):
                os.remove("dbgallerynsunittest.db")

    class ConventionRelationship(unittest.TestCase):
        def setUp(self):
            if os.path.exists("dbconunittest.db"):
                os.remove("dbconunittest.db")
            engine = create_engine("sqlite:///dbconunittest.db")
            Session.configure(bind=engine)
            Base.metadata.create_all(engine)

            self.session = Session()

            self.con = Convention()
            self.con.name = "Con1"
            self.galleries = [Gallery(title="title"+str(x)) for x in range(10)]
            self.con.galleries.extend(self.galleries)
            self.session.add(self.con)
            self.session.commit()
            self.assertEqual(self.session.query(Convention).count(), 1)
            self.assertEqual(self.con.id, self.galleries[0].convention_id)

        def test_delete(self):
            self.session.query(Convention).delete()
            self.session.commit()

            self.assertIsNone(self.galleries[0].convention)
            self.assertEqual(self.session.query(Gallery).count(), 10)
            self.assertEqual(self.session.query(Convention).count(), 0)

        def test_delete2(self):
            self.session.delete(self.galleries[0])
            self.session.commit()

            self.assertEqual(self.session.query(Gallery).count(), 9)
            self.assertEqual(self.session.query(Convention).count(), 1)

        def test_no_orphans(self):
            self.session.query(Gallery).delete()
            self.session.commit()

            self.assertEqual(self.session.query(Gallery).count(), 0)
            self.assertEqual(self.session.query(Convention).count(), 0)

        def tearDown(self):
            self.session.close()
            if os.path.exists("dbconunittest.db"):
                os.remove("dbconunittest.db")


    class ChapterRelationship(unittest.TestCase):
        def setUp(self):
            if os.path.exists("dbchapunittest.db"):
                os.remove("dbchapunittest.db")
            engine = create_engine("sqlite:///dbchapunittest.db")
            Session.configure(bind=engine)
            Base.metadata.create_all(engine)

            self.session = Session()

            self.chapters = [Chapter(title="ch"+str(x)) for x in range(20)]

            self.galleries = [Gallery(title="title"+str(x)) for x in range(10)]
            self.session.add_all(self.galleries)
            chaps = doublegen(self.chapters)
            for n, x in enumerate(self.galleries):
                x.chapters.extend(next(chaps))
            self.session.commit()

            for g in self.galleries:
                self.assertEqual(g.chapters.count(), 2)

        def test_delete(self):
            self.session.query(Chapter).delete()
            self.session.commit()

            self.assertEqual(self.session.query(Gallery).count(), 10)
            self.assertEqual(self.session.query(Chapter).count(), 0)

        def test_delete2(self):
            self.session.delete(self.galleries[0])
            self.session.commit()

            self.assertEqual(self.session.query(Gallery).count(), 9)
            self.assertEqual(self.session.query(Chapter).count(), 18)

        def test_delete3(self):
            self.session.delete(self.galleries[0].chapters[0])
            self.session.commit()

            self.assertEqual(self.session.query(Gallery).count(), 10)
            self.assertEqual(self.session.query(Chapter).count(), 19)

        def test_no_orphans(self):
            for g in self.galleries:
                self.session.delete(g)
            self.session.commit()

            self.assertEqual(self.session.query(Gallery).count(), 0)
            self.assertEqual(self.session.query(Chapter).count(), 0)

        def tearDown(self):
            self.session.close()
            if os.path.exists("dbchapunittest.db"):
                os.remove("dbchapunittest.db")

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
            self.chapter = Chapter()
            self.gallery.chapters.append(self.chapter)
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

            self.gallery = Gallery(title="title1")
            self.namespaces = [Namespace(name="ns"+str(x)) for x in range(20)]
            self.tags = [Tag(name="tag"+str(x)) for x in range(10)]
            self.chapters = [Chapter(title="ch"+str(x)) for x in range(5)]
            self.session.add(self.gallery)
            self.gallery.chapters.extend(self.chapters)
            self.nstags = []
            nsgen = doublegen(self.namespaces)
            for x, tag in enumerate(self.tags):
                doublens = next(nsgen)
                self.nstags.append(NamespaceTags(doublens[0], tag))
                self.nstags.append(NamespaceTags(doublens[1], tag))

            for x, ch in enumerate(self.chapters):
                ch.tags.extend(self.nstags)
            self.session.commit()

            self.assertEqual(self.session.query(Gallery).count(), 1)
            self.assertEqual(self.session.query(Chapter).count(), 5)
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
            self.session.delete(self.chapters[0])
            self.session.commit()
            self.assertEqual(self.session.query(Gallery).count(), 1)
            self.assertEqual(self.session.query(Chapter).count(), 4)
            self.assertTrue(self.session.query(NamespaceTags).count() != 0)
            self.assertTrue(self.session.query(Tag).count() != 0)
            self.assertTrue(self.session.query(Namespace).count() != 0)

        def test_no_orphans(self):
            self.session.delete(self.gallery)
            self.session.commit()
            self.assertEqual(self.session.query(Gallery).count(), 0)
            self.assertEqual(self.session.query(Chapter).count(), 0)

            self.session.query(Namespace).delete()
            self.session.commit()
            self.assertEqual(self.session.query(Tag).count(), 0)
            self.assertEqual(self.session.query(Namespace).count(), 0)
            self.assertEqual(self.session.query(NamespaceTags).count(), 0)

        def tearDown(self):
            self.session.close()
            if os.path.exists("dbtagunittest.db"):
                os.remove("dbtagunittest.db")

    unittest.main(verbosity=2)