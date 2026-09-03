"""Helpers to load the standalone example applications."""
import importlib.util
import os
import sys

EXAMPLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'examples')

# every example ships its own copy of these modules
LOCAL_MODULES = ('helpers', 'forms', 'ckeditor', 'cache', 'dropzone', 'mail')


def load_app(example, module_name, env=None):
    """Import the app.py of the given example as a standalone module.

    ``env`` temporarily overrides environment variables while the module is
    imported. The examples read their settings (the database URL in
    particular) at import time, so an override applied afterwards is ignored.
    """
    directory = os.path.abspath(os.path.join(EXAMPLES_DIR, example))
    path = os.path.join(directory, 'app.py')

    # drop the copies loaded by the previously imported example
    for module in LOCAL_MODULES:
        sys.modules.pop(module, None)

    original_env = {key: os.environ.get(key) for key in env or {}}
    os.environ.update(env or {})
    original_cwd = os.getcwd()
    sys.path.insert(0, directory)
    os.chdir(directory)
    try:
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    finally:
        os.chdir(original_cwd)
        sys.path.remove(directory)
        for key, value in original_env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
