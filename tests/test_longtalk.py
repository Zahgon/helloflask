import unittest

from starlette.testclient import TestClient

from . import load_app


class LongtalkTestCase(unittest.TestCase):
    def setUp(self):
        # Import longtalk app specifically
        longtalk_app = load_app('longtalk', 'longtalk_app')

        self.app = longtalk_app.app
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
