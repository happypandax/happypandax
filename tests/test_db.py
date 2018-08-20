import unittest
import pytest
import os
import sys
import arrow
import itertools
import datetime

pytestmark = pytest.mark.dbtest

sys.path.insert(0, os.path.abspath('..'))
from sqlalchemy.orm import sessionmaker
from happypanda.common import constants
from happypanda.core.db import *

constants.gallery_grouping_init = False


def doublegen(it):
    l = it.copy()
    while it:
        yield (l.pop(), l.pop())

def create_db():
    config.dialect.value = constants.Dialect.SQLITE
    engine = create_engine("sqlite://")
    init(engine=engine)
    return constants._db_scoped_session.session_factory()

class GeneralTest(unittest.TestCase):
    def setUp(self):
        self.session = create_db()
        self.gallery = Gallery()
        self.session.add(self.gallery)
        self.session.commit()

    @unittest.expectedFailure
    def test_exists(self):
        self.gallery.artists.append(Artist())
        self.session.commit()
        self.assertEqual(self.session.query(Artist).count(), 1)

        p = "hello/here.zip"
        self.gallery.path = p
        self.session.commit()
        g = Gallery()
        g.path = p
        self.assertTrue(g.exists())
        g.path = "nope"
        self.assertFalse(g.exists())
            
        self.session.commit()
        g.path = p
        self.assertTrue(g.exists())


    def test_types(self):
        self.gallery.title = ""
        self.gallery.fav = True
        self.gallery.times_read = 2
        self.gallery.pub_date = arrow.now()
        self.gallery.timestamp = arrow.now()
        self.gallery.last_read = arrow.now()
        self.gallery.last_read = datetime.datetime.utcnow()
        self.assertTrue(isinstance(self.gallery.last_read, arrow.Arrow))
        self.session.commit()

    def test_history(self):
        self.assertEqual(self.session.query(Event).count(), 0) #

        self.gallery.read(constants.default_user.id)
        self.assertEqual(self.session.query(Event).count(), 1)
        self.gallery.read(constants.default_user.id)
        self.session.commit()
        self.assertEqual(self.session.query(Event).count(), 2)

        self.gallery.delete()

        self.assertEqual(self.session.query(Event).count(), 2)

    def test_typesfail(self):
        with self.assertRaises(AssertionError):
            self.gallery.last_read = datetime.date.today()
        with self.assertRaises(AssertionError):
            self.gallery.single_source = 2
        with self.assertRaises(AssertionError):
            self.gallery.rating = ""

    def test_url(self):
        self.gallery.urls.append(Url(name="http://www.google.com"))
        self.session.commit()
        self.assertEqual(len(self.gallery.urls), 1)

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
        titles = [Title() for x in range(10)]
        for x in titles:
            x.language = lang
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
        artists = [Artist() for x in range(10)]

        self.gallery.artists.extend(artists)

        self.session.commit()

        self.assertGreater(len(self.gallery.artists), 0)
        self.assertTrue(artists[0].galleries[0].id == self.gallery.id)

    def test_page_numbering(self):
        pages = [Page() for x in range(10)]
        self.assertEqual(pages[0].number, -1)
        for p in pages:
            self.gallery.pages.append(p)
        self.session.commit()
        for n, i in enumerate(self.gallery.pages.all(), 1):
            self.assertEqual(i.number, n)
        self.gallery.pages.reorder()
        for n, i in enumerate(self.gallery.pages.all(), 1):
            self.assertEqual(i.number, n)
        self.session.commit()
        p0 = pages[0]
        p1 = pages[1]
        self.gallery.pages.remove(p0)
        self.assertEqual(p1.number, 1)
        with pytest.raises(exceptions.DatabaseError) as excinfo:
            self.gallery.pages.insert(4, p0)
        self.assertEqual(self.gallery.pages.count(), 9)
        p = Page()
        self.assertEqual(p.number, -1)
        self.gallery.pages.insert(0, p)
        self.assertEqual(p.number, 1)
        self.assertEqual(p1.number, 2)
        self.session.commit()
        self.assertEqual(self.gallery.pages.count(), 10)
        for n, i in enumerate(self.gallery.pages.all(), 1):
            self.assertEqual(i.number, n)

    @unittest.expectedFailure
    def test_page_numbering2(self):
        self.session.delete(self.gallery.pages[0])
        self.session.commit()
        for n, i in enumerate(self.gallery.pages.all(), 1):
            self.assertEqual(i.number, n)

    def tearDown(self):
        self.session.close()

class ItemUpdateTest(unittest.TestCase):
    def setUp(self):
        self.session = create_db()

    def test_general(self):
        self.gallery = Gallery()
        with self.assertRaises(AssertionError) as e:
            self.gallery.update("artists", "a1", op="test")


    def test_gallery(self):
        self.gallery = Gallery()
        d = arrow.now()
        self.gallery.update("last_read", d)
        self.assertEqual(self.gallery.last_read, d)
        self.gallery.update("single_source", False)
        self.assertEqual(self.gallery.single_source, False)
        self.gallery.update("number", 1)
        self.assertEqual(self.gallery.number, 1)
        
        self.gallery.update("grouping", name="test")
        self.assertIsNotNone(self.gallery.grouping)
        self.assertEqual(self.gallery.grouping.name, "test")

        self.gallery.update("language", Language(name="test2"))
        self.assertIsNotNone(self.gallery.language)
        self.assertEqual(self.gallery.language.name, "test2")

        self.gallery.update("category", "test3")
        self.assertIsNotNone(self.gallery.category)
        self.assertEqual(self.gallery.category.name, "test3")

        with self.assertRaises(AttributeError) as e:
            self.gallery.update("artists", "a1")

        anames = ["a1", "a2", "a3"]
        self.gallery.update("artists", names=anames)
        self.assertIsNotNone(self.gallery.artists)
        self.assertEqual(len(self.gallery.artists), 1)
        self.assertEqual(len(self.gallery.artists[0].names), 3)
        for a in self.gallery.artists[0].names:
            self.assertTrue(a.name in anames)
            anames.remove(a.name)

        self.gallery.update("pages", Page())
        self.assertEqual(self.gallery.pages.count(), 1)
        self.gallery.update("pages", [Page() for x in range(9)])
        self.assertEqual(self.gallery.pages.count(), 10)

    def test_metatags(self):
        self.gallery = Gallery()
        mtags = {x: True for x in MetaTag.names}
        l = len(mtags)
        self.assertGreater(l, 3)
        self.assertEqual(len(self.gallery.metatags), 0)
        self.gallery.update("metatags", mtags)
        self.assertEqual(len(self.gallery.metatags), l)
        mtags[MetaTag.names.inbox] = False
        self.gallery.update("metatags", mtags)
        self.assertEqual(len(self.gallery.metatags), l-1)
        mtags[MetaTag.names.favorite] = False
        self.gallery.update("metatags", mtags)
        self.assertEqual(len(self.gallery.metatags), l-2)
        mtags[MetaTag.names.inbox] = True
        self.gallery.update("metatags", mtags)
        self.assertEqual(len(self.gallery.metatags), l-1)
        for x in mtags:
            mtags[x] = False
        self.gallery.update("metatags", mtags)
        self.assertEqual(len(self.gallery.metatags), 0)

        self.gallery.update("metatags", MetaTag(name="test"))
        self.assertEqual(len(self.gallery.metatags), 1)
        self.assertEqual(self.gallery.metatags[0].name, "test")
        for x in mtags:
            mtags[x] = True
        self.gallery.update("metatags", mtags)
        self.assertEqual(len(self.gallery.metatags), l+1)
        self.gallery.metatags.clear()
        self.assertEqual(len(self.gallery.metatags), 0)

        m = MetaTag(name="test")
        self.gallery.update("metatags", [MetaTag(name="test"+str(x)) for x in range(5)])
        self.assertEqual(len(self.gallery.metatags), 5)
        self.gallery.update("metatags", m)
        self.assertEqual(len(self.gallery.metatags), 6)
        self.gallery.update("metatags", m, op="remove")
        self.assertEqual(len(self.gallery.metatags), 5)

        self.gallery.update("metatags", "test", op="remove")
        self.assertEqual(len(self.gallery.metatags), 5)
        self.gallery.update("metatags", "test", op="add")
        self.assertEqual(len(self.gallery.metatags), 6)
        self.gallery.update("metatags", "test", op="remove")
        self.assertEqual(len(self.gallery.metatags), 5)

    def tearDown(self):
        self.session.close()

class GalleryRelationship(unittest.TestCase):
    def setUp(self):
        self.session = create_db()

        self.pages = [Page(name="p" + str(x)) for x in range(20)]
        self.galleries = [Gallery() for x in range(10)]
        nsgen = doublegen(self.pages)
        for x, g in enumerate(self.galleries):
            g.pages.extend(next(nsgen))

        self.session.add_all(self.galleries)
        self.session.commit()

        self.assertEqual(self.session.query(Gallery).count(), 10)
        self.assertEqual(self.session.query(Page).count(), 20)

    @unittest.expectedFailure
    def test_first_page(self):
        self.assertEqual(self.galleries[0].first_page, self.galleries[0].pages[0])
        self.assertEqual(self.galleries[0].first_page.number, 1)
        self.assertEqual(self.galleries[0].pages[0].number, 1)
        self.assertEqual(self.galleries[0].pages[1].number, 2)
        spage = self.galleries[0].pages[1]
        self.session.delete(self.galleries[0].first_page)
        self.session.commit()
        self.assertEqual(self.galleries[0].pages[0].number, 1)
        self.assertEqual(self.galleries[0].pages[0], spage)
        self.assertEqual(self.galleries[0].first_page, spage)
        self.assertEqual(self.session.query(Gallery).count(), 10)
        self.assertEqual(self.session.query(Page).count(), 19)

    def test_delete(self):
        self.session.delete(self.galleries[0])
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 9)
        self.assertEqual(self.session.query(Page).count(), 18)

    def test_delete2(self):
        self.session.delete(self.pages[0])
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 10)
        self.assertEqual(self.session.query(Page).count(), 19)
        self.assertEqual(self.galleries[9].pages.count(), 1)

    def test_delete4(self):
        self.session.delete(self.pages[0])
        self.session.delete(self.pages[1])
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 10)
        self.assertEqual(self.session.query(Page).count(), 18)
        self.assertEqual(self.galleries[9].pages.count(), 0)

    def test_no_orphans(self):
        self.session.query(Gallery).delete()
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 0)
        self.assertEqual(self.session.query(Page).count(), 0)

    def test_no_orphans2(self):
        self.session.query(Page).delete()
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 10)
        self.assertEqual(self.session.query(Page).count(), 0)

    def test_no_orphans3(self):
        for g in self.galleries:
            self.session.delete(g)
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 0)
        self.assertEqual(self.session.query(Page).count(), 0)

    def test_no_orphans4(self):
        for g in self.pages:
            self.session.delete(g)
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 10)
        self.assertEqual(self.session.query(Page).count(), 0)

    def tearDown(self):
        self.session.close()

class CollectionRelationship(unittest.TestCase):
    def setUp(self):
        self.session = create_db()

        self.collections = [Collection() for x in range(2)]
        for n, x in enumerate(self.collections):
            x.name = "col"+str(n)
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
        self.assertEqual(self.session.query(Collection).count(), 2)

    def tearDown(self):
        self.session.close()

class ListRelationship(unittest.TestCase):
    def setUp(self):
        self.session = create_db()

        self.glists = [GalleryFilter() for x in range(2)]
        for n, x in enumerate(self.glists):
            x.name = "list"+str(n)
        self.galleries = [Gallery() for x in range(10)]
        self.session.add_all(self.galleries)
        for gl in self.glists:
            gl.galleries.extend(self.galleries)
        self.session.commit()

    def test_delete(self):
        self.session.delete(self.glists[0])
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 10)
        self.assertEqual(self.session.query(GalleryFilter).count(), 1)

    def test_delete2(self):
        self.session.delete(self.galleries[0])
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 9)
        self.assertEqual(self.session.query(GalleryFilter).count(), 2)
        self.assertEqual(self.glists[0].galleries.count(), 9)

    def test_no_orphans(self):
        self.session.query(Gallery).delete()
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 0)
        self.assertEqual(self.session.query(GalleryFilter).count(), 2)
        self.assertEqual(self.glists[0].galleries.count(), 0)

    def test_no_orphans2(self):
        self.session.query(GalleryFilter).delete()
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 10)
        self.assertEqual(self.session.query(GalleryFilter).count(), 0)

    def tearDown(self):
        self.session.close()

class ArtistRelationship(unittest.TestCase):
    def setUp(self):
        self.session = create_db()

        self.artist = Artist()
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
        for g in self.galleries:
            self.session.delete(g)
        #self.session.query(Gallery).delete() # does not trigger after_flush event
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 0)
        self.assertEqual(self.session.query(Artist).count(), 0)

    def tearDown(self):
        self.session.close()

class ArtistNameRelationship(unittest.TestCase):
    def setUp(self):
        self.session = create_db()

        self.gallery = Gallery()
        self.artist = Artist()
        self.gallery.artists.append(self.artist)
        self.names = [ArtistName(name='name'+str(x)) for x in range(10)]
        root = self.names[0]
        for n in self.names[1:]:
            n.alias_for = root
        self.session.add(self.gallery)
        self.artist.names.append(root)
        self.session.commit()
        assert not self.names[0].alias_for

        self.assertEqual(len(self.artist.names), 1)
        self.assertEqual(root.aliases.count(), 9)
        self.assertEqual(self.session.query(ArtistName).count(), 10)

    def test_delete(self):
        self.session.delete(self.names[1])
        self.session.commit()
        self.assertEqual(self.session.query(Artist).count(), 1)
        self.assertEqual(self.session.query(ArtistName).count(), 9)
        self.assertEqual(self.artist.names[0], self.names[0])

    def test_delete2(self):
        self.session.delete(self.names[0])
        self.session.commit()
        self.assertEqual(self.session.query(Artist).count(), 1)
        self.assertEqual(self.session.query(ArtistName).count(), 0)

    def test_orphans_when_alias(self):
        self.session.delete(self.artist)
        self.session.commit()
        self.assertEqual(self.session.query(Artist).count(), 0)
        self.assertEqual(self.session.query(ArtistName).count(), 9)

    def test_orphans(self):
        self.session.delete(self.names[0])
        self.session.delete(self.artist)
        self.session.commit()
        self.assertEqual(self.session.query(Artist).count(), 0)
        self.assertEqual(self.session.query(ArtistName).count(), 0)


    def tearDown(self):
        self.session.close()

class ParodyRelationship(unittest.TestCase):
    def setUp(self):
        self.session = create_db()

        self.parody = Parody()
        self.galleries = [Gallery() for x in range(10)]
        self.session.add_all(self.galleries)
        self.parody.galleries.extend(self.galleries)
        self.session.commit()

        self.assertEqual(self.parody.id, self.galleries[0].parodies[0].id)

    def test_delete(self):
        self.session.delete(self.parody)
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 10)
        self.assertEqual(self.session.query(Parody).count(), 0)

    def test_delete2(self):
        self.session.delete(self.galleries[0])
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 9)
        self.assertEqual(self.session.query(Parody).count(), 1)

    def test_no_orphans(self):
        for g in self.galleries:
            self.session.delete(g)
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 0)
        self.assertEqual(self.session.query(Parody).count(), 0)

    def tearDown(self):
        self.session.close()

class ParodyNameRelationship(unittest.TestCase):
    def setUp(self):
        self.session = create_db()

        self.gallery = Gallery()
        self.parody = Parody()
        self.gallery.parodies.append(self.parody)
        self.names = [ParodyName(name='name'+str(x)) for x in range(10)]
        root = self.names[0]
        for n in self.names[1:]:
            n.alias_for = root
        self.session.add(self.gallery)
        self.parody.names.append(root)
        self.session.commit()

        self.assertEqual(len(self.parody.names), 1)
        self.assertEqual(root.aliases.count(), 9)
        self.assertEqual(self.session.query(ParodyName).count(), 10)

    def test_delete(self):
        self.session.delete(self.names[1])
        self.session.commit()
        self.assertEqual(self.session.query(Parody).count(), 1)
        self.assertEqual(self.session.query(ParodyName).count(), 9)
        self.assertEqual(self.parody.names[0], self.names[0])

    def test_delete2(self):
        self.session.delete(self.names[0])
        self.session.commit()
        self.assertEqual(self.session.query(Parody).count(), 1)
        self.assertEqual(self.session.query(ParodyName).count(), 0)

    def test_orphans_when_alias(self):
        self.session.delete(self.parody)
        self.session.commit()
        self.assertEqual(self.session.query(Parody).count(), 0)
        self.assertEqual(self.session.query(ParodyName).count(), 9)

    def test_no_orphans(self):
        self.session.delete(self.names[0])
        self.session.delete(self.parody)
        self.session.commit()
        self.assertEqual(self.session.query(Parody).count(), 0)
        self.assertEqual(self.session.query(ParodyName).count(), 0)

    def tearDown(self):
        self.session.close()

class CircleRelationship(unittest.TestCase):
    def setUp(self):
        self.session = create_db()

        self.gallery = Gallery()
        self.circle = Circle()
        self.circle.name = "Circle1"
        self.artists = [Artist() for x in range(10)]
        self.session.add_all(self.artists)
        self.circle.artists.extend(self.artists)
        self.gallery.artists.extend(self.artists)
        self.session.commit()

        self.assertEqual(self.circle.id, self.artists[0].circles[0].id)


    def test_delete(self):
        self.session.delete(self.circle)
        self.session.commit()
        self.assertEqual(self.session.query(Artist).count(), 10)
        self.assertEqual(self.session.query(Circle).count(), 0)

    def test_delete2(self):
        self.session.delete(self.artists[0])
        self.session.commit()
        self.assertEqual(self.session.query(Artist).count(), 9)
        self.assertEqual(self.session.query(Circle).count(), 1)

    def test_no_orphans(self):
        for g in self.artists:
            self.session.delete(g)
        self.session.commit()
        self.assertEqual(self.session.query(Artist).count(), 0)
        self.assertEqual(self.session.query(Circle).count(), 0)

    def tearDown(self):
        self.session.close()

class HashRelationship(unittest.TestCase):
    def setUp(self):
        self.session = create_db()

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

class GroupingRelationship(unittest.TestCase):
    def setUp(self):
        self.session = create_db()

        self.galleryns = [Grouping(name="gns" + str(x)) for x in range(2)]
        self.galleries = [Gallery() for x in range(10)]
        self.galleryns[0].galleries.extend(self.galleries[:5])
        self.galleryns[1].galleries.extend(self.galleries[5:])
        self.session.add_all(self.galleryns)
        self.session.commit()

        self.assertEqual(self.session.query(Grouping).count(), 2)
        self.assertEqual(self.session.query(Gallery).count(), 10)
        self.assertEqual(self.galleries[0].grouping_id, self.galleryns[0].id)

    def test_delete(self):
        self.session.delete(self.galleryns[0])
        self.session.commit()

        self.assertEqual(self.session.query(Grouping).count(), 1)
        self.assertEqual(self.session.query(Gallery).count(), 10)

    def test_delete2(self):
        self.session.delete(self.galleries[0])
        self.session.commit()

        self.assertEqual(self.session.query(Grouping).count(), 2)
        self.assertEqual(self.session.query(Gallery).count(), 9)

    def test_no_orphans(self):
        for g in self.galleries:
            self.session.delete(g)
        self.session.commit()

        self.assertEqual(self.session.query(Grouping).count(), 0)
        self.assertEqual(self.session.query(Gallery).count(), 0)

    def test_change_ns(self):
        self.galleryns[1].galleries.append(self.galleries[0])
        self.session.commit()

        self.assertEqual(self.session.query(Grouping).count(), 2)
        self.assertEqual(self.session.query(Gallery).count(), 10)
        self.assertEqual(self.galleryns[1].galleries.count(), 6)
        self.assertEqual(self.galleryns[0].galleries.count(), 4)

    def test_gallery_numbering(self):
        for gns in self.galleryns:
            for n, i in enumerate(gns.galleries.all(), 1):
                self.assertEqual(i.number, n)
        self.galleryns[0].galleries.reorder()
        self.galleryns[1].galleries.reorder()
        for gns in self.galleryns:
            for n, i in enumerate(gns.galleries.all(), 1):
                self.assertEqual(i.number, n)
        p0 = self.galleryns[0].galleries[0]
        p1 = self.galleryns[0].galleries[1]
        self.galleryns[0].galleries.remove(p0)
        self.assertEqual(p1.number, 1)
        self.assertEqual(self.galleryns[0].galleries.count(), 4)
        p = Gallery()
        self.assertEqual(p.number, -1)
        self.galleryns[0].galleries.insert(0, p)
        self.assertEqual(p.number, 1)
        self.assertEqual(p1.number, 2)
        self.session.commit()
        self.assertEqual(self.galleryns[0].galleries.count(), 5)
        for n, i in enumerate(self.galleryns[0].galleries.all(), 1):
            self.assertEqual(i.number, n)


    def tearDown(self):
        self.session.close()

class LanguageRelationship(unittest.TestCase):
    def setUp(self):
        self.session = create_db()

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

class CategoryRelationship(unittest.TestCase):
    def setUp(self):
        self.session = create_db()

        self.cat = Category()
        self.cat.name = "Con1"
        self.galleries = [Gallery() for x in range(10)]
        self.cat.galleries.extend(self.galleries)
        self.session.add(self.cat)
        self.session.commit()
        self.assertEqual(self.session.query(Category).count(), 1)
        self.assertEqual(self.cat.id, self.galleries[0].category_id)

    def test_delete(self):
        self.session.query(Category).delete()
        self.session.commit()

        self.assertIsNone(self.galleries[0].category)
        self.assertEqual(self.session.query(Gallery).count(), 10)
        self.assertEqual(self.session.query(Category).count(), 0)

    def test_delete2(self):
        self.session.delete(self.galleries[0])
        self.session.commit()

        self.assertEqual(self.session.query(Gallery).count(), 9)
        self.assertEqual(self.session.query(Category).count(), 1)

    def test_orphans(self):
        self.session.query(Gallery).delete()
        self.session.commit()

        self.assertEqual(self.session.query(Gallery).count(), 0)
        self.assertEqual(self.session.query(Category).count(), 1)

    def tearDown(self):
        self.session.close()

class StatusRelationship(unittest.TestCase):
    def setUp(self):
        self.session = create_db()

        self.status = Status()
        self.status.name = "Stat1"
        self.galleryns = [Grouping(name="gns" + str(x)) for x in range(2)]
        self.galleries = [Gallery() for x in range(10)]
        self.galleryns[0].galleries.extend(self.galleries[:5])
        self.galleryns[1].galleries.extend(self.galleries[5:])
        for gns in self.galleryns:
            gns.status = self.status
        self.session.add_all(self.galleryns)
        self.session.add(self.status)
        self.session.commit()
        self.assertEqual(self.session.query(Status).count(), 1+len(Status.names))
        self.assertEqual(self.session.query(Grouping).count(), 2)
        self.assertEqual(self.session.query(Gallery).count(), 10)
        self.assertEqual(self.status, self.galleryns[0].status)

    def test_delete(self):
        self.session.query(Status).delete()
        self.session.commit()

        self.assertIsNone(self.galleryns[0].status)
        self.assertEqual(self.session.query(Grouping).count(), 2)
        self.assertEqual(self.session.query(Status).count(), 0)

    def test_delete2(self):
        self.session.delete(self.galleryns[0])
        self.session.commit()

        self.assertEqual(self.session.query(Grouping).count(), 1)
        self.assertEqual(self.session.query(Status).count(), 1+len(Status.names))

    def test_orphans(self):
        self.session.query(Grouping).delete()
        self.session.commit()

        self.assertEqual(self.session.query(Grouping).count(), 0)
        self.assertEqual(self.session.query(Status).count(), 1+len(Status.names))

    def tearDown(self):
        self.session.close()

class UrlRelationship(unittest.TestCase):
    def setUp(self):
        self.session = create_db()

        self.gallery = Gallery()
        self.session.add(self.gallery)
        self.session.commit()

        self.urls = [Url(name="http://google.com") for x in range(10)]
        self.gallery.urls.extend(self.urls)
        self.session.commit()

        self.assertEqual(self.session.query(Url).count(), 10)

    def test_delete(self):
        self.session.delete(self.urls[0])
        self.session.commit()

        self.assertEqual(self.session.query(Url).count(), 9)
        self.assertEqual(self.session.query(Gallery).count(), 1)

    def test_no_orphans(self):
        self.session.delete(self.gallery)
        self.session.commit()

        self.assertEqual(self.session.query(Url).count(), 0)
        self.assertEqual(self.session.query(Gallery).count(), 0)

    def tearDown(self):
        self.session.close()

class TagRelationship(unittest.TestCase):
    def setUp(self):
        self.session = create_db()

        self.namespaces = [Namespace(name="ns" + str(x)) for x in range(20)]
        self.tags = [Tag(name="tag" + str(x)) for x in range(10)]
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

        self.nstag1, self.nstag2, self.nstag3, self.nstag4, *_ = self.nstags

    def test_tag_parent(self):
        with no_autoflush(self.session):
            for y in self.galleries:
                y.tags = []
        self.gal1, self.gal2, *_ = self.galleries
        self.test_tag_aliases()
        self.nstag2.parent = self.nstag1
        self.session.commit()
        self.assertEqual(self.nstag2.parent, self.nstag1)
        self.assertEqual(self.nstag1.children[0], self.nstag2)

        with self.assertRaises(exceptions.DatabaseError) as e:
            self.nstag2.parent = self.nstag3
            self.assertTrue("Cannot make NamespaceTag itself's child" in e.msg)

        self.assertEqual(self.nstag2.aliases.count(), 2)
        self.nstag3.alias_for = None
        self.session.flush()
        self.nstag2.parent = self.nstag3
        self.session.commit()
        self.assertEqual(self.nstag2.aliases.count(), 1)
        self.assertEqual(self.nstag2.parent, self.nstag3)
        self.assertEqual(self.nstag3.children[0], self.nstag2)
        self.assertEqual(self.nstag1.children.count(), 0)

        # test when alias is given a parent

        self.assertEqual(self.nstag1.parent, None)
        self.nstag4.alias_for = self.nstag1
        self.nstag4.parent = self.nstag2
        self.session.commit()
        self.assertEqual(self.nstag2.aliases.count(), 0)
        self.assertEqual(self.nstag2.children.count(), 1)
        self.assertEqual(self.nstag2.children[0], self.nstag1)
        self.assertEqual(self.nstag4.parent, None)

    def test_tag_aliases(self):
        self.nstag3.alias_for = self.nstag2
        self.session.commit()
        self.assertEqual(self.nstag3.alias_for, self.nstag2)
        self.assertEqual(self.nstag2.aliases[0], self.nstag3)
        self.nstag4.alias_for = self.nstag3
        self.session.commit()
        self.assertEqual(self.nstag4.alias_for, self.nstag2)
        self.assertEqual(self.nstag2.aliases[1], self.nstag4)

        self.assertEqual(self.nstag1.tag.aliases.count(), 0)
        self.assertIsNone(self.nstag2.tag.alias_for)


    def test_original_tag_galleries(self):
        self.gal1, self.gal2, *_ = self.galleries
        with no_autoflush(self.session):
            for y in self.galleries:
                y.tags = []

        self.test_tag_aliases()
        self.gal1.tags.append(self.nstag3)
        self.gal1.tags.append(self.nstag4)

        self.session.commit()
        self.assertEqual(self.gal1.tags.count(), 1)
        self.assertEqual(self.gal1.tags[0], self.nstag2)
        self.assertTrue(self.nstag3 not in self.gal1.tags)
        self.assertTrue(self.nstag4 not in self.gal1.tags)

    def test_append_tag_galleries(self):
        with no_autoflush(self.session):
            for y in self.galleries:
                y.tags = []
        self.gal1, self.gal2, *_ = self.galleries
        
        self.test_tag_aliases()

        self.nstag4.parent = self.nstag1

        self.gal1.tags.append(self.nstag3)
        self.gal1.tags.append(self.nstag4)

        self.session.commit()
        self.assertEqual(self.gal1.tags.count(), 2)
        self.assertTrue(self.nstag1 in self.gal1.tags)
        self.assertTrue(self.nstag2 in self.gal1.tags)

        # test delete child

        self.gal1.tags.remove(self.nstag2)
        self.session.commit()
        self.assertEqual(self.gal1.tags.count(), 1)
        self.assertTrue(self.nstag1 in self.gal1.tags)
        self.assertTrue(self.nstag2 not in self.gal1.tags)

        # readd

        self.gal1.tags.append(self.nstag4)
        self.session.commit()
        self.assertEqual(self.gal1.tags.count(), 2)
        self.assertTrue(self.nstag1 in self.gal1.tags)
        self.assertTrue(self.nstag2 in self.gal1.tags)

        ## test delete parent

        self.assertTrue(self.nstag1 in self.gal1.tags)
        self.gal1.tags.remove(self.nstag1)
        self.session.commit()
        self.assertEqual(self.gal1.tags.count(), 0)
        self.assertTrue(self.nstag1 not in self.gal1.tags)
        self.assertTrue(self.nstag2 not in self.gal1.tags)


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
        for g in self.galleries:
            self.session.delete(g)
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 0)

        for g in self.namespaces:
            self.session.delete(g)
        self.session.commit()
        self.assertEqual(self.session.query(Namespace).count(), 0)
        self.assertEqual(self.session.query(NamespaceTags).count(), 0)
        self.assertEqual(self.session.query(Tag).count(), 0)

    def test_no_orphans2(self):
        for g in self.namespaces:
            self.session.delete(g)
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 5)
        self.assertEqual(self.session.query(Namespace).count(), 0)
        self.assertEqual(self.session.query(NamespaceTags).count(), 0)
        self.assertEqual(self.session.query(Tag).count(), 0)

    def test_no_orphans3(self):
        for g in self.nstags:
            self.session.delete(g)
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 5)
        self.assertEqual(self.session.query(Namespace).count(), 0)
        self.assertEqual(self.session.query(NamespaceTags).count(), 0)
        self.assertEqual(self.session.query(Tag).count(), 0)

    def test_no_orphans4(self):
        for g in self.nstags[1:]:
            self.session.delete(g)
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 5)
        self.assertEqual(self.session.query(Namespace).count(), 1)
        self.assertEqual(self.session.query(NamespaceTags).count(), 1)
        self.assertEqual(self.session.query(Tag).count(), 1)

    def test_no_orphans5(self):
        self.galleries[0].tags.remove(self.nstags[0])
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 5)
        self.assertEqual(self.session.query(Namespace).count(), 20)
        self.assertEqual(self.session.query(NamespaceTags).count(), 20)
        self.assertEqual(self.session.query(Tag).count(), 10)

    def tearDown(self):
        self.session.close()

class ProfileRelationship(unittest.TestCase):
    def setUp(self):
        self.session = create_db()

        self.gns = [Grouping(name="gns" + str(x)) for x in range(5)]
        self.galleries = [Gallery() for x in range(5)]
        self.collections = [Collection() for x in range(5)]
        for n, x in enumerate(self.collections):
            x.name = "title"+str(n)
        self.pages = [Page(number=x) for x in range(5)]

        for n, x in enumerate(self.galleries):
            self.collections[n].galleries.append(x)
            self.pages[n].gallery = x
            self.gns[n].galleries.append(x)

        self.session.add_all(self.galleries)
        self.session.commit()

        self.assertEqual(self.session.query(Gallery).count(), 5)
        self.assertEqual(self.session.query(Grouping).count(), 5)
        self.assertEqual(self.session.query(Collection).count(), 5)
        self.assertEqual(self.session.query(Page).count(), 5)

        self.profiles = [Profile(path="p" + str(x), data='test', size='200') for x in range(5)]

        profile_nmb = itertools.cycle(range(5))

        for x in (self.gns, self.galleries, self.collections, self.pages):
            for y in x:
                y.profiles.append(self.profiles[next(profile_nmb)])

        self.session.commit()

        self.assertEqual(self.session.query(Profile).count(), 5)


    def test_delete(self):
        self.session.delete(self.profiles[0])
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 5)
        self.assertEqual(self.session.query(Grouping).count(), 5)
        self.assertEqual(self.session.query(Collection).count(), 5)
        self.assertEqual(self.session.query(Page).count(), 5)
        self.assertEqual(self.session.query(Profile).count(), 4)

    def test_delete2(self):
        self.session.delete(self.pages[0])
        self.session.commit()
        self.assertEqual(self.session.query(Gallery).count(), 5)
        self.assertEqual(self.session.query(Grouping).count(), 5)
        self.assertEqual(self.session.query(Collection).count(), 5)
        self.assertEqual(self.session.query(Page).count(), 4)
        self.assertEqual(self.session.query(Profile).count(), 5)

    def test_no_orphans(self):
        for x in (self.gns,):
            for y in x:
                self.session.delete(y)
        self.session.commit()

        self.assertEqual(self.session.query(Gallery).count(), 5)
        self.assertEqual(self.session.query(Grouping).count(), 0)
        self.assertEqual(self.session.query(Collection).count(), 5)
        self.assertEqual(self.session.query(Page).count(), 5)
        self.assertEqual(self.session.query(Profile).count(), 5)

    def test_no_orphans2(self):
        for x in (self.gns, self.galleries, self.collections):
            for y in x:
                self.session.delete(y)
        self.session.commit()

        self.assertEqual(self.session.query(Gallery).count(), 0)
        self.assertEqual(self.session.query(Grouping).count(), 0)
        self.assertEqual(self.session.query(Collection).count(), 0)
        self.assertEqual(self.session.query(Page).count(), 0)
        self.assertEqual(self.session.query(Profile).count(), 0)

    def tearDown(self):
        self.session.close()

