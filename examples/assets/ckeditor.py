"""A FastAPI port of the Flask-CKEditor extension."""
from fastapi.responses import JSONResponse
from markupsafe import Markup
from wtforms import TextAreaField
from wtforms.widgets import TextArea

CKEDITOR_VERSION = '4.22.1'

DEFAULT_CONFIG = {
    'CKEDITOR_PKG_TYPE': 'standard',
    'CKEDITOR_LANGUAGE': '',
    'CKEDITOR_HEIGHT': 0,
    'CKEDITOR_WIDTH': 0,
    'CKEDITOR_CODE_THEME': 'monokai_sublime',
    'CKEDITOR_FILE_UPLOADER': '',
    'CKEDITOR_FILE_BROWSER': '',
    'CKEDITOR_UPLOAD_ERROR_MESSAGE': 'Upload failed.',
    'CKEDITOR_ENABLE_CODESNIPPET': False,
    'CKEDITOR_EXTRA_PLUGINS': [],
}


class CKEditorWidget(TextArea):
    def __call__(self, field, **kwargs):
        class_ = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = f'ckeditor {class_}'
        return super().__call__(field, **kwargs)


class CKEditorField(TextAreaField):
    widget = CKEditorWidget()


class CKEditor:
    """Register the ``ckeditor`` object used by the templates."""

    def __init__(self, app, templates):
        self.app = app
        self.settings = app.state.config
        for key, value in DEFAULT_CONFIG.items():
            self.settings.setdefault(key, value)
        templates.env.globals['ckeditor'] = self

    def get_url(self, endpoint_or_url):
        if not endpoint_or_url:
            return endpoint_or_url
        if endpoint_or_url.startswith(('https://', 'http://', '/')):
            return endpoint_or_url
        return str(self.app.url_path_for(endpoint_or_url))

    def load(self, custom_url=None, pkg_type=None, version=CKEDITOR_VERSION):
        """Load the CKEditor resource from the CDN."""
        pkg_type = pkg_type or self.settings['CKEDITOR_PKG_TYPE']
        if self.settings['CKEDITOR_ENABLE_CODESNIPPET'] and not pkg_type.endswith('all'):
            pkg_type = 'standard-all'
        url = custom_url or f'https://cdn.ckeditor.com/{version}/{pkg_type}/ckeditor.js'
        return Markup(f'<script src="{url}"></script>')

    def config(self, name='ckeditor', custom_config='', **kwargs):
        """Configure the CKEditor instance attached to the given input field."""
        def _get_config(key):
            return kwargs.get(key, self.settings[f'CKEDITOR_{key.upper()}'])

        extra_plugins = list(_get_config('extra_plugins'))
        file_uploader = self.get_url(_get_config('file_uploader'))
        file_browser = self.get_url(_get_config('file_browser'))

        if (file_uploader or file_browser) and 'filebrowser' not in extra_plugins:
            extra_plugins.append('filebrowser')

        if _get_config('enable_codesnippet') and 'codesnippet' not in extra_plugins:
            extra_plugins.append('codesnippet')

        return Markup(f'''
<script type="text/javascript">
    document.getElementById("{name}").classList.remove("ckeditor");
    CKEDITOR.replace( "{name}", {{
        language: "{_get_config('language')}",
        height: {_get_config('height')},
        width: {_get_config('width')},
        codeSnippet_theme: "{_get_config('code_theme')}",
        imageUploadUrl: "{file_uploader}",
        filebrowserUploadUrl: "{file_uploader}",
        filebrowserBrowseUrl: "{file_browser}",
        extraPlugins: "{','.join(extra_plugins)}",
        versionCheck: false,
        {custom_config}
    }});
</script>''')

    def create(self, name='ckeditor', value=''):
        """Create a CKEditor textarea directly."""
        return Markup(f'<textarea class="ckeditor" name="{name}" id="{name}">{value}</textarea>')

    def load_code_theme(self, version=CKEDITOR_VERSION):
        """Load the resources used to highlight the code snippets."""
        theme = self.settings['CKEDITOR_CODE_THEME']
        pkg_type = self.settings['CKEDITOR_PKG_TYPE']
        if not pkg_type.endswith('all'):
            pkg_type = 'standard-all'
        base_url = f'https://cdn.ckeditor.com/{version}/{pkg_type}/plugins/codesnippet/lib/highlight'
        js_url = f'{base_url}/highlight.pack.js'
        css_url = f'{base_url}/styles/{theme}.css'
        return Markup(f'''<link href="{css_url}" rel="stylesheet">\n<script src="{js_url}"></script>\n
            <script>hljs.initHighlightingOnLoad();</script>''')


def upload_success(url, filename='', message=None):
    """Return an upload success response, for CKEditor >= 4.5."""
    data = {'uploaded': 1, 'url': url, 'filename': filename}
    if message is not None:
        data['error'] = {'message': message}
    return JSONResponse(data)


def upload_fail(message='Upload failed.'):
    """Return an upload failed response, for CKEditor >= 4.5."""
    return JSONResponse({'uploaded': 0, 'error': {'message': message}})
