from unittest import TestCase
from facegraph import graph, url_operations
from facegraph.fql import FQL
from mock import patch

class UrlOperationsTests(TestCase):
    def testadd_path(self):
        url = u'http://a.com'
        self.assertEquals('http://a.com/', url_operations.add_path(url, ''))
        self.assertEquals('http://a.com/path', url_operations.add_path(url, 'path'))
        self.assertEquals('http://a.com/path', url_operations.add_path(url, '/path'))
        self.assertEquals('http://a.com/path/', url_operations.add_path(url, 'path/'))
        self.assertEquals('http://a.com/path/', url_operations.add_path(url, '/path/'))

        url = u'http://a.com/'
        self.assertEquals('http://a.com/path', url_operations.add_path(url, 'path'))
        self.assertEquals('http://a.com/path', url_operations.add_path(url, '/path'))
        self.assertEquals('http://a.com/path/', url_operations.add_path(url, 'path/'))
        self.assertEquals('http://a.com/path/', url_operations.add_path(url, '/path/'))

        url = u'http://a.com/path1'
        self.assertEquals('http://a.com/path1/path2', url_operations.add_path(url, 'path2'))
        self.assertEquals('http://a.com/path1/path2', url_operations.add_path(url, '/path2'))
        self.assertEquals('http://a.com/path1/path2/', url_operations.add_path(url, 'path2/'))
        self.assertEquals('http://a.com/path1/path2/', url_operations.add_path(url, '/path2/'))

        url = u'http://a.com/path1/'
        self.assertEquals('http://a.com/path1/path2', url_operations.add_path(url, 'path2'))
        self.assertEquals('http://a.com/path1/path2', url_operations.add_path(url, '/path2'))
        self.assertEquals('http://a.com/path1/path2/', url_operations.add_path(url, 'path2/'))
        self.assertEquals('http://a.com/path1/path2/', url_operations.add_path(url, '/path2/'))

    def test_query_param(self):
        self.assertEquals(('a', 'b'), url_operations._query_param('a', 'b'))

    def test_query_param_unicode(self):
        # unicode objects should be encoded as utf-8 bytes
        self.assertEquals(('a', 'b'), url_operations._query_param('a', u'b'))
        self.assertEquals(('a', '\xc3\xa9'), url_operations._query_param('a', u'\xe9'))

        # bytes should be remain as bytes
        self.assertEquals(('a', '\xc3\xa9'), url_operations._query_param('a', '\xc3\xa9'))

    def test_add_query_params(self):
        url = u'http://a.com'
        self.assertEquals('http://a.com?a=b', url_operations.add_query_params(url, ('a', 'b')))
        self.assertEquals('http://a.com?a=b', url_operations.add_query_params(url, {'a': 'b'}))
        self.assertEquals('http://a.com?a=%C3%A9', url_operations.add_query_params(url, {'a': '\xc3\xa9'}))

        url = u'http://a.com/path'
        self.assertEquals('http://a.com/path?a=b', url_operations.add_query_params(url, {'a': 'b'}))

        url = u'http://a.com?a=b'
        self.assertEquals('http://a.com?a=b&a=c', url_operations.add_query_params(url, ('a', 'c')))
        self.assertEquals('http://a.com?a=b&c=d', url_operations.add_query_params(url, ('c', 'd')))

    def test_update_query_params(self):
        url = u'http://a.com?a=b'
        self.assertEquals('http://a.com?a=b', url_operations.update_query_params(url, {}))
        self.assertEquals('http://a.com?a=c', url_operations.update_query_params(url, ('a', 'c')))
        self.assertEquals('http://a.com?a=b&c=d', url_operations.update_query_params(url, {'c': 'd'}))
        self.assertEquals('http://a.com?a=%C4%A9', url_operations.update_query_params(url, {'a': '\xc4\xa9'}))

        url = u'http://a.com/path?a=b'
        self.assertEquals('http://a.com/path?a=c', url_operations.update_query_params(url, {'a': 'c'}))

    def test_escaping(self):
        url = u'http://a.com'
        self.assertEquals('http://a.com?my+key=c', url_operations.add_query_params(url, ('my key', 'c')))
        self.assertEquals('http://a.com?c=my+val', url_operations.add_query_params(url, ('c', 'my val')))

    def test_no_double_escaping_existing_params(self):
        url = 'http://a.com?a=%C4%A9'
        self.assertEquals('http://a.com?a=%C4%A9&c=d', url_operations.update_query_params(url, {'c': 'd'}))

        url = 'http://a.com?a=my+val'
        self.assertEquals('http://a.com?a=my+val&c=d', url_operations.update_query_params(url, {'c': 'd'}))

class GraphUrlTests(TestCase):
    def setUp(self):
        self.graph = graph.Graph()

    def test_initial_state(self):
        self.assertEquals(graph.Graph.API_ROOT, self.graph.url)

    def test_getitem(self):
        expected = 'https://graph.facebook.com/path'
        self.assertEquals(expected, self.graph.path.url)

        expected = 'https://graph.facebook.com/path/path2'
        self.assertEquals(expected, self.graph.path.path2.url)

    def test_getitem_slice(self):
        url = self.graph[0:20].url
        self.assertTrue(url.startswith('https://graph.facebook.com/?'))
        self.assertTrue('offset=0' in url)
        self.assertTrue('limit=20' in url)

    def test_getattr(self):
        expected = 'https://graph.facebook.com/path'
        self.assertEquals(expected, self.graph['path'].url)

        expected = 'https://graph.facebook.com/path/path2'
        self.assertEquals(expected, self.graph['path']['path2'].url)

    def test_update_params(self):
        expected = 'https://graph.facebook.com/?a=b'
        self.graph = self.graph & {'a': 'b'}
        self.assertEquals(expected, self.graph.url)
        expected += '&c=d'
        self.assertEquals(expected, (self.graph & {'c': 'd'}).url)

    def test_set_params(self):
        expected = 'https://graph.facebook.com/?a=b'
        self.graph = self.graph | {'a': 'b'}
        self.assertEquals(expected, self.graph.url)

        expected = 'https://graph.facebook.com/?a=c'
        self.assertEquals(expected, (self.graph | {'a': 'c'}).url)

        expected = 'https://graph.facebook.com/?a=b&c=d'
        self.assertEquals(expected, (self.graph | {'c': 'd'}).url)

    def test_fields(self):
        expected = 'https://graph.facebook.com/?fields=a%2Cb'
        self.graph = self.graph.fields('a', 'b')
        self.assertEquals(expected, self.graph.url)

    def test_ids(self):
        expected = 'https://graph.facebook.com/?ids=a%2Cb'
        self.graph = self.graph.ids('a', 'b')
        self.assertEquals(expected, self.graph.url)

class FQLTests(TestCase):
    def setUp(self):
        self.fql = FQL(access_token='abc123')

    @patch('facegraph.fql.FQL.fetch_json')
    def test_call(self, mock_fetch):
        self.fql('my_query')
        url = mock_fetch.call_args[0][0]
        self.assertTrue(url.startswith('https://api.facebook.com/method/fql.query?'))
        self.assertTrue('query=my_query' in url)
        self.assertTrue('access_token=abc123' in url)

    @patch('facegraph.fql.FQL.fetch_json')
    def test_call_with_arbitrary_params(self, mock_fetch):
        self.fql('my_query', key='value')
        url = mock_fetch.call_args[0][0]
        self.assertTrue(url.startswith('https://api.facebook.com/method/fql.query?'))
        self.assertTrue('query=my_query' in url)
        self.assertTrue('access_token=abc123' in url)
        self.assertTrue('key=value' in url)

    @patch('facegraph.fql.FQL.fetch_json')
    def test_multi(self, mock_fetch):
        self.fql.multi(['my_query1', 'my_query2'])
        url = mock_fetch.call_args[0][0]
        self.assertTrue(url.startswith('https://api.facebook.com/method/fql.multiquery?'))
        print url
        self.assertTrue("&queries=%5B%22my_query1%22%2C+%22my_query2%22%5D" in url)
