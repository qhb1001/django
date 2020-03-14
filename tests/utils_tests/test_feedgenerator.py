import datetime
from io import StringIO

from django.test import SimpleTestCase
from django.utils import feedgenerator
from django.utils.timezone import get_fixed_timezone, utc
from django.utils.xmlutils import SimplerXMLGenerator


class FeedgeneratorTests(SimpleTestCase):
    """
    Tests for the low-level syndication feed framework.
    """

    def test_get_tag_uri(self):
        """
        get_tag_uri() correctly generates TagURIs.
        """
        self.assertEqual(
            feedgenerator.get_tag_uri('http://example.org/foo/bar#headline', datetime.date(2004, 10, 25)),
            'tag:example.org,2004-10-25:/foo/bar/headline')

    def test_get_tag_uri_with_port(self):
        """
        get_tag_uri() correctly generates TagURIs from URLs with port numbers.
        """
        self.assertEqual(
            feedgenerator.get_tag_uri(
                'http://www.example.org:8000/2008/11/14/django#headline',
                datetime.datetime(2008, 11, 14, 13, 37, 0),
            ),
            'tag:www.example.org,2008-11-14:/2008/11/14/django/headline')

    def test_rfc2822_date(self):
        """
        rfc2822_date() correctly formats datetime objects.
        """
        self.assertEqual(
            feedgenerator.rfc2822_date(datetime.datetime(2008, 11, 14, 13, 37, 0)),
            "Fri, 14 Nov 2008 13:37:00 -0000"
        )

    def test_rfc2822_date_with_timezone(self):
        """
        rfc2822_date() correctly formats datetime objects with tzinfo.
        """
        self.assertEqual(
            feedgenerator.rfc2822_date(datetime.datetime(2008, 11, 14, 13, 37, 0, tzinfo=get_fixed_timezone(60))),
            "Fri, 14 Nov 2008 13:37:00 +0100"
        )

    def test_rfc2822_date_without_time(self):
        """
        rfc2822_date() correctly formats date objects.
        """
        self.assertEqual(
            feedgenerator.rfc2822_date(datetime.date(2008, 11, 14)),
            "Fri, 14 Nov 2008 00:00:00 -0000"
        )

    def test_rfc3339_date(self):
        """
        rfc3339_date() correctly formats datetime objects.
        """
        self.assertEqual(
            feedgenerator.rfc3339_date(datetime.datetime(2008, 11, 14, 13, 37, 0)),
            "2008-11-14T13:37:00Z"
        )

    def test_rfc3339_date_with_timezone(self):
        """
        rfc3339_date() correctly formats datetime objects with tzinfo.
        """
        self.assertEqual(
            feedgenerator.rfc3339_date(datetime.datetime(2008, 11, 14, 13, 37, 0, tzinfo=get_fixed_timezone(120))),
            "2008-11-14T13:37:00+02:00"
        )

    def test_rfc3339_date_without_time(self):
        """
        rfc3339_date() correctly formats date objects.
        """
        self.assertEqual(
            feedgenerator.rfc3339_date(datetime.date(2008, 11, 14)),
            "2008-11-14T00:00:00Z"
        )

    def test_atom1_mime_type(self):
        """
        Atom MIME type has UTF8 Charset parameter set
        """
        atom_feed = feedgenerator.Atom1Feed("title", "link", "description")
        self.assertEqual(
            atom_feed.content_type, "application/atom+xml; charset=utf-8"
        )

    def test_rss_mime_type(self):
        """
        RSS MIME type has UTF8 Charset parameter set
        """
        rss_feed = feedgenerator.Rss201rev2Feed("title", "link", "description")
        self.assertEqual(
            rss_feed.content_type, "application/rss+xml; charset=utf-8"
        )

    # Two regression tests for #14202

    def test_feed_without_feed_url_gets_rendered_without_atom_link(self):
        feed = feedgenerator.Rss201rev2Feed('title', '/link/', 'descr')
        self.assertIsNone(feed.feed['feed_url'])
        feed_content = feed.writeString('utf-8')
        self.assertNotIn('<atom:link', feed_content)
        self.assertNotIn('href="/feed/"', feed_content)
        self.assertNotIn('rel="self"', feed_content)

    def test_feed_with_feed_url_gets_rendered_with_atom_link(self):
        feed = feedgenerator.Rss201rev2Feed('title', '/link/', 'descr', feed_url='/feed/')
        self.assertEqual(feed.feed['feed_url'], '/feed/')
        feed_content = feed.writeString('utf-8')
        self.assertIn('<atom:link', feed_content)
        self.assertIn('href="/feed/"', feed_content)
        self.assertIn('rel="self"', feed_content)

    def test_atom_add_item(self):
        # Not providing any optional arguments to Atom1Feed.add_item()
        feed = feedgenerator.Atom1Feed('title', '/link/', 'descr')
        feed.add_item('item_title', 'item_link', 'item_description')
        feed.writeString('utf-8')

    def test_deterministic_attribute_order(self):
        feed = feedgenerator.Atom1Feed('title', '/link/', 'desc')
        feed_content = feed.writeString('utf-8')
        self.assertIn('href="/link/" rel="alternate"', feed_content)

    def test_latest_post_date_returns_utc_time(self):
        for use_tz in (True, False):
            with self.settings(USE_TZ=use_tz):
                rss_feed = feedgenerator.Rss201rev2Feed('title', 'link', 'description')
                self.assertEqual(rss_feed.latest_post_date().tzinfo, utc)

    def test_rssfeed(self):
        # initialization
        feed = feedgenerator.RssFeed('title', '/link/', 'descr', language='language_test',
                                     categories=['categories_test'], feed_copyright='feed_copyright_test',
                                     ttl='ttl_test')
        feed._version = 'v2.0'
        feed.add_item('title', 'link', 'desc', language='English')

        # get the content
        feed_content = feed.writeString('utf-8')

        # check the content
        self.assertIn('language_test', feed_content)
        self.assertIn('categories_test', feed_content)
        self.assertIn('feed_copyright_test', feed_content)
        self.assertIn('ttl_test', feed_content)

    def test_rssuserland091feed_writestring(self):
        # initialization
        feed = feedgenerator.RssUserland091Feed('titile', '/link/', 'descr_test')
        feed._version = 'v2.0'

        # create handler
        s = StringIO()
        handler = SimplerXMLGenerator(s, 'utf-8')
        handler.startDocument()

        # add item
        feed.add_item_elements(handler,
                               item={'title': 'title_test', 'link': 'link_test', 'description': 'description'})

        # get the content
        feed_content = s.getvalue()

        # check the content
        self.assertIn('title_test', feed_content)
        self.assertIn('link_test', feed_content)
        self.assertIn('description', feed_content)

    def test_Rss201rev2Feed(self):
        # initialization
        feed = feedgenerator.Rss201rev2Feed('titile', '/link/', 'descr_test')
        feed._version = 'v2.0'

        # create handler
        s = StringIO()
        handler = SimplerXMLGenerator(s, 'utf-8')
        handler.startDocument()

        # add item
        feed.add_item_elements(handler, item={'title': 'title_test', 'link': 'link_test',
                                              'description': 'description_test',
                                              'author_name': 'qinhongbo', 'author_email': 'hongbo.qin.1001@gmail.com',
                                              'pubdate': datetime.datetime(2015, 10, 1), 'comments': 'comments_test',
                                              'unique_id': 'unique_id_test', 'ttl': 'ttl_test',
                                              'enclosures': [
                                                  feedgenerator.Enclosure('url_test', '100', 'mime_type_test')],
                                              'categories': ['categories_test']})

        # get the content
        feed_content = s.getvalue()

        # check the content
        self.assertIn('title_test', feed_content)
        self.assertIn('link_test', feed_content)
        self.assertIn('description_test', feed_content)
        self.assertIn('qinhongbo', feed_content)
        self.assertIn('hongbo.qin.1001@gmail.com', feed_content)
        self.assertIn('comments_test', feed_content)
        self.assertIn('unique_id_test', feed_content)
        self.assertIn('ttl_test', feed_content)
        self.assertIn('categories_test', feed_content)

    def test_Atom1Feed(self):
        # initialization
        feed = feedgenerator.Atom1Feed('titile', '/link/', 'descr_test', subtitle='subtitle_test',
                                       feed_url="feed_url_test", language='English',
                                       feed_copyright='feed_copyright_test', author_email='test@email',
                                       author_name='qhb', author_link='author_link_test', categories=['categories_test'])
        feed._version = 'v2.0'
        feed.add_item('titile', '/link/', 'descr_test', language='English', feed_url='feed_url_test',
                      subtitle='subtitle_test',
                      categories=['categories_test'], feed_copyright='feed_copyright_test',
                      pubdate=datetime.datetime(2015, 10, 1),
                      updateddate=datetime.datetime(2015, 10, 2),
                      author_name='qhb', author_link='link_test', author_email='email_test',
                      unique_id='unique_id_test',
                      enclosure=[feedgenerator.Enclosure('url_test', '100', 'type_test')],
                      item_copyright='item_copyright_test')

        # get the content
        feed_content = feed.writeString('utf-8')

        # check the content
        self.assertIn('feed_url_test', feed_content)
        self.assertIn('subtitle_test', feed_content)
        self.assertIn('English', feed_content)
        self.assertIn('qhb', feed_content)
        self.assertIn('test@email', feed_content)
        self.assertIn('feed_copyright_test', feed_content)
        self.assertIn('author_link_test', feed_content)
        self.assertIn('categories_test', feed_content)
