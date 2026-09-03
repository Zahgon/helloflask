import unittest

from starlette.testclient import TestClient

from . import load_app


class Ch3TestCase(unittest.TestCase):
    def setUp(self):
        # Import ch3 app specifically
        ch3_app = load_app('ch3', 'ch3_app')

        self.app = ch3_app.app
        self.app.state.config['TESTING'] = True
        self.client = TestClient(self.app)

    def test_app_exist(self):
        self.assertIsNotNone(self.app)

    def test_app_is_testing(self):
        self.assertTrue(self.app.state.config['TESTING'])

    def test_watchlist_page(self):
        response = self.client.get('/watchlist')
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('Grey Li', data)
        self.assertIn('My Neighbor Totoro', data)
        self.assertIn('The Matrix', data)
        self.assertIn('CoCo', data)
