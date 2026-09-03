import unittest

from click.testing import CliRunner
from starlette.testclient import TestClient

from . import load_app


class Ch1TestCase(unittest.TestCase):
    def setUp(self):
        # Import ch1 app specifically
        ch1_app = load_app('ch1', 'ch1_app')

        self.app = ch1_app.app
        self.app.state.config['TESTING'] = True
        self.client = TestClient(self.app)
        self.cli = ch1_app.cli
        self.cli_runner = CliRunner()

    def test_app_exist(self):
        self.assertIsNotNone(self.app)

    def test_app_is_testing(self):
        self.assertTrue(self.app.state.config['TESTING'])

    def test_index_page(self):
        response = self.client.get('/')
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('Hello, world!', data)

    def test_ping_page(self):
        response = self.client.get('/ping')
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('Hello, Flask!', data)

    def test_pong_page(self):
        response = self.client.get('/pong')
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('Hello, Flask!', data)

    def test_greet_default(self):
        response = self.client.get('/greet')
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('Hello, Programmer!', data)

    def test_greet_with_name(self):
        response = self.client.get('/greet/Flask')
        data = response.text
        self.assertEqual(response.status_code, 200)
        self.assertIn('Hello, Flask!', data)

    def test_hello_cli_command(self):
        result = self.cli_runner.invoke(self.cli, ['hello'])
        self.assertIn('Hello, Human!', result.output)
