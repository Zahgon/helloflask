import unittest

from click.testing import CliRunner
from starlette.testclient import TestClient

from . import load_app

IN_MEMORY_DB = {'DATABASE_URL': 'sqlite:///:memory:'}


class Ch5TestCase(unittest.TestCase):
    def setUp(self):
        # Import ch5 app specifically, against a throwaway in-memory database
        ch5_app = load_app('ch5', 'ch5_app', env=IN_MEMORY_DB)

        self.app = ch5_app.app
        self.base = ch5_app.Base
        self.engine = ch5_app.engine
        self.app.state.config['TESTING'] = True
        self.client = TestClient(self.app)
        self.cli = ch5_app.cli
        self.cli_runner = CliRunner()

        self.base.metadata.create_all(self.engine)

    def tearDown(self):
        self.base.metadata.drop_all(self.engine)

    def test_app_exist(self):
        self.assertIsNotNone(self.app)

    def test_app_is_testing(self):
        self.assertTrue(self.app.state.config['TESTING'])

    def test_cli_init_command(self):
        result = self.cli_runner.invoke(self.cli, ['init'])
        self.assertIn('Initialized.', result.output)

    def test_database_models(self):
        # Import ch5 app specifically for models
        ch5_models = load_app('ch5', 'ch5_models', env=IN_MEMORY_DB)

        # Test model creation doesn't raise errors
        self.assertIsNotNone(ch5_models.Note)
        self.assertIsNotNone(ch5_models.Author)
        self.assertIsNotNone(ch5_models.Article)
        self.assertIsNotNone(ch5_models.Country)
        self.assertIsNotNone(ch5_models.Capital)
