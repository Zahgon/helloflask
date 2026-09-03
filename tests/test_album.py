import unittest
import os
from pathlib import Path

from starlette.testclient import TestClient

from . import load_app


class AlbumTestCase(unittest.TestCase):
    def setUp(self):
        # Import album app specifically
        album_app = load_app('album', 'album_app')

        self.app = album_app.app
        self.app.state.config['TESTING'] = True
        self.app.state.config['CSRF_ENABLED'] = False
        # Use temp directory for testing uploads
        self.app.state.config['UPLOAD_PATH'] = Path(album_app.BASE_DIR) / 'test_uploads'
        self.client = TestClient(self.app)

        # Create test upload directory
        os.makedirs(self.app.state.config['UPLOAD_PATH'], exist_ok=True)

    def tearDown(self):
        # Clean up test upload directory
        import shutil
        if os.path.exists(self.app.state.config['UPLOAD_PATH']):
            shutil.rmtree(self.app.state.config['UPLOAD_PATH'])

    def test_app_exist(self):
        self.assertIsNotNone(self.app)

    def test_app_is_testing(self):
        self.assertTrue(self.app.state.config['TESTING'])

    def test_index_page(self):
        response = self.client.get('/')
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('HelloFlask', data)

    def test_upload_page_get(self):
        response = self.client.get('/upload')
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('Upload Photo', data)

    def test_upload_no_file(self):
        response = self.client.post('/upload', data={})
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('This field is required', data)
