import unittest

from starlette.testclient import TestClient

from . import load_app


class Ch4TestCase(unittest.TestCase):
    def setUp(self):
        # Import ch4 app specifically
        ch4_app = load_app('ch4', 'ch4_app')

        self.app = ch4_app.app
        self.app.state.config['TESTING'] = True
        self.app.state.config['CSRF_ENABLED'] = False
        self.client = TestClient(self.app)

    def test_app_exist(self):
        self.assertIsNotNone(self.app)

    def test_app_is_testing(self):
        self.assertTrue(self.app.state.config['TESTING'])

    def test_index_page(self):
        response = self.client.get('/')
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('Home', data)

    def test_html_form_get(self):
        response = self.client.get('/html')
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', data)

    def test_html_form_post(self):
        response = self.client.post('/html', data={'username': 'testuser'}, follow_redirects=True)
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('Welcome home, testuser!', data)

    def test_basic_form_get(self):
        response = self.client.get('/basic')
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', data)

    def test_basic_form_post_valid(self):
        response = self.client.post('/basic', data={
            'username': 'testuser',
            'password': 'password123'
        }, follow_redirects=True)
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('Welcome home, testuser!', data)

    def test_basic_form_post_invalid(self):
        response = self.client.post('/basic', data={
            'username': 'testuser',
            'password': '123'  # Too short
        })
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('Field must be between 8 and 128 characters long', data)
