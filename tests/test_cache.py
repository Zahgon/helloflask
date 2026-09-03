import unittest

from starlette.testclient import TestClient

from . import load_app


class CacheTestCase(unittest.TestCase):
    def setUp(self):
        # Import cache app specifically
        cache_app = load_app('cache', 'cache_app')

        self.app = cache_app.app
        self.app.state.config['TESTING'] = True
        self.client = TestClient(self.app)

    def test_app_exist(self):
        self.assertIsNotNone(self.app)

    def test_app_is_testing(self):
        self.assertTrue(self.app.state.config['TESTING'])

    def test_index_page(self):
        response = self.client.get('/')
        data = response.text
        self.assertEqual(response.status_code, 200)
