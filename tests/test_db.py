import unittest, os, sys, itertools
sys.path.insert(0, os.path.abspath('..'))
from sqlalchemy.orm import sessionmaker
from happypanda.common import constants
from happypanda.core.db import *
Session = sessionmaker()
constants.db_session = Session
initEvents()



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
        constants.db_session = Session
        self.session = Session()
        initDefaults(self.session)
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
        initDefaults(self.session)

        self.collections = [Collection(title="col"+str(x)) for x in range(2)]
        self.galleries = [Gallery() for x in range(10)]
        self.session.add_all(self.galleries)
        self.collections[0].galleries.extend(self.galleries[:5])
        self.collections[1].galleries.extend(self.galleries[5:])
        self.session.commit()

        self.assertEqual(self.session.query(Gallery).count(), 10)
        self.assertEqual(self.session.query(Collection).count(), 3) # the default collection is also there

    def default(self):
        initDefaults(self.session)
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
        self.assertEqual(self.session.query(Collection).count(), 2) # the default collection is also there

    def test_delete2(self):
        self.session.delete(self.galleries[0])
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 9)
        self.assertEqual(self.session.query(Collection).count(), 3) # the default collection is also there
        self.assertEqual(len(self.collections[0].galleries), 4)

    def test_delete3(self):
        for c in self.collections:
            self.session.delete(c)
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 10)
        self.assertEqual(self.session.query(Collection).count(), 1) # the default collection is also there

    def test_no_orphans(self):
        self.session.query(Gallery).delete()
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 0)
        self.assertEqual(self.session.query(Collection).count(), 1) # the default collection is also there

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
        initDefaults(self.session)

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
        initDefaults(self.session)

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
        initDefaults(self.session)

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
        initDefaults(self.session)

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
        initDefaults(self.session)

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
        initDefaults(self.session)

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
        initDefaults(self.session)

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
        initDefaults(self.session)

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
        initDefaults(self.session)

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
        initDefaults(self.session)

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
        initDefaults(self.session)

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
        self.assertEqual(self.session.query(Collection).count(), 6)
        self.assertEqual(self.session.query(Page).count(), 5)
        self.assertEqual(self.session.query(List).count(), 5)

        self.profiles = [Profile(path="p"+str(x), type=x) for x in range(5)]

        profile_nmb = itertools.cycle(range(5))

        for x in (self.lists, self.gns, self.galleries, self.collections, self.pages):
            for y in x:
                y.profiles.append(self.profiles[next(profile_nmb)])

        self.session.commit()

        self.assertEqual(self.session.query(Profile).count(), 5)


    def test_delete(self):
        self.session.delete(self.profiles[0])
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 5)
        self.assertEqual(self.session.query(GalleryNamespace).count(), 5)
        self.assertEqual(self.session.query(Collection).count(), 6)
        self.assertEqual(self.session.query(Page).count(), 5)
        self.assertEqual(self.session.query(List).count(), 5)
        self.assertEqual(self.session.query(Profile).count(), 4)

    def test_delete2(self):
        self.session.delete(self.pages[0])
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 5)
        self.assertEqual(self.session.query(GalleryNamespace).count(), 5)
        self.assertEqual(self.session.query(Collection).count(), 6)
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
        self.assertEqual(self.session.query(Collection).count(), 1)
        self.assertEqual(self.session.query(Page).count(), 0)
        self.assertEqual(self.session.query(List).count(), 0)
        self.assertEqual(self.session.query(Profile).count(), 0)

    def tearDown(self):
        self.session.close()
        if os.path.exists("dbprofileunittest.db"):
            os.remove("dbprofileunittest.db")

