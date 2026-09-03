import unittest

from starlette.testclient import TestClient

from . import load_app


class Ch2TestCase(unittest.TestCase):
    def setUp(self):
        # Import ch2 app specifically
        ch2_app = load_app('ch2', 'ch2_app')

        self.app = ch2_app.app
        self.app.state.config['TESTING'] = True
        self.client = TestClient(self.app)

    def test_app_exist(self):
        self.assertIsNotNone(self.app)

    def test_app_is_testing(self):
        self.assertTrue(self.app.state.config['TESTING'])

    def test_hello_page(self):
        response = self.client.get('/')
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('Hello, Human!', data)
        self.assertIn('[Not Authenticated]', data)

    def test_hello_with_name_query(self):
        response = self.client.get('/?name=Flask')
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('Hello, Flask!', data)

    def test_hello_route(self):
        response = self.client.get('/hello')
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('Hello, Human!', data)

    def test_hi_redirect(self):
        response = self.client.get('/hi', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        data = response.text
        self.assertIn('Hello, Human!', data)

    def test_time_machine(self):
        response = self.client.get('/back/2020')
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('Welcome to 4!', data)

    def test_three_colors(self):
        for color in ['blue', 'white', 'red']:
            response = self.client.get(f'/colors/{color}')
            self.assertEqual(response.status_code, 200)
            data = response.text
            self.assertIn('Love is patient and kind', data)

    def test_teapot_coffee(self):
        response = self.client.get('/brew/coffee')
        self.assertEqual(response.status_code, 418)

    def test_teapot_tea(self):
        response = self.client.get('/brew/tea')
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('A drop of tea', data)

    def test_404_error(self):
        response = self.client.get('/answer')
        self.assertEqual(response.status_code, 404)

    def test_note_text(self):
        response = self.client.get('/note')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'].split(';')[0], 'text/plain')
        data = response.text
        self.assertIn('Note', data)
        self.assertIn('Morty', data)

    def test_note_html(self):
        response = self.client.get('/note/html')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'].split(';')[0], 'text/html')
        data = response.text
        self.assertIn('<h1>Note</h1>', data)

    def test_note_xml(self):
        response = self.client.get('/note/xml')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'].split(';')[0], 'application/xml')
        data = response.text
        self.assertIn('<?xml version="1.0"', data)

    def test_note_json(self):
        response = self.client.get('/note/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['content-type'].split(';')[0], 'application/json')
        json_data = response.json()
        self.assertIn('note', json_data)
        self.assertEqual(json_data['note']['to'], 'Morty')

    def test_note_invalid_format(self):
        response = self.client.get('/note/invalid')
        self.assertEqual(response.status_code, 400)

    def test_set_cookie(self):
        response = self.client.get('/set/TestUser', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('name=TestUser', response.headers.get('Set-Cookie', ''))

    def test_login(self):
        self.client.cookies.clear()
        response = self.client.get('/login', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        data = response.text
        self.assertIn('[Authenticated]', data)

    def test_admin_access_denied(self):
        self.client.cookies.clear()
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 403)

    def test_admin_access_granted(self):
        self.client.get('/login')  # log the user in to fill the session
        response = self.client.get('/admin')
        self.assertEqual(response.status_code, 200)
        data = response.text
        self.assertIn('Welcome to admin page', data)

    def test_logout(self):
        self.client.get('/login')  # log the user in to fill the session
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        data = response.text
        self.assertIn('[Not Authenticated]', data)

    def test_foo_page(self):
        response = self.client.get('/foo')
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('Foo page', data)
        self.assertIn('Do something and redirect', data)

    def test_bar_page(self):
        response = self.client.get('/bar')
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('Bar page', data)
        self.assertIn('Do something and redirect', data)

    def test_do_something_redirect(self):
        response = self.client.get('/do-something?next=/foo', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
