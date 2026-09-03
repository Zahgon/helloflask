# -*- coding: utf-8 -*-
"""A FastAPI port of the Flask-Dropzone extension."""
from markupsafe import Markup

DROPZONE_VERSION = '5.9.3'

# defined normal file type
ALLOWED_FILE_EXTENSIONS = {
    'default': 'image/*, audio/*, video/*, text/*, application/*',
    'image': 'image/*',
    'audio': 'audio/*',
    'video': 'video/*',
    'text': 'text/*',
    'app': 'application/*',
}

DEFAULT_CONFIG = {
    'DROPZONE_MAX_FILE_SIZE': 3,  # MB
    'DROPZONE_INPUT_NAME': 'file',
    'DROPZONE_ALLOWED_FILE_CUSTOM': False,
    'DROPZONE_ALLOWED_FILE_TYPE': 'default',
    'DROPZONE_MAX_FILES': 'null',
    'DROPZONE_TIMEOUT': None,
    'DROPZONE_REDIRECT_VIEW': None,
    'DROPZONE_UPLOAD_MULTIPLE': False,
    'DROPZONE_PARALLEL_UPLOADS': 2,
    'DROPZONE_IN_FORM': False,
    # messages
    'DROPZONE_DEFAULT_MESSAGE': 'Drop files here or click to upload.',
    'DROPZONE_INVALID_FILE_TYPE': "You can't upload files of this type.",
    'DROPZONE_FILE_TOO_BIG': 'File is too big {{filesize}}. Max filesize: {{maxFilesize}}MiB.',
    'DROPZONE_SERVER_ERROR': 'Server error: {{statusCode}}',
    'DROPZONE_BROWSER_UNSUPPORTED': "Your browser does not support drag'n'drop file uploads.",
    'DROPZONE_MAX_FILE_EXCEED': "You can't upload any more files.",
    'DROPZONE_CANCEL_UPLOAD': 'Cancel upload',
    'DROPZONE_REMOVE_FILE': 'Remove file',
    'DROPZONE_CANCEL_CONFIRMATION': 'You really want to delete this file?',
    'DROPZONE_UPLOAD_CANCELED': 'Upload canceled',
}


class Dropzone:
    """Register the ``dropzone`` object used by the templates."""

    def __init__(self, app, templates):
        self.app = app
        self.settings = app.state.config
        for key, value in DEFAULT_CONFIG.items():
            self.settings.setdefault(key, value)
        templates.env.globals['dropzone'] = self

    def get_url(self, endpoint_or_url, **kwargs):
        if not endpoint_or_url:
            return None
        if endpoint_or_url.startswith(('https://', 'http://', '/')):
            return endpoint_or_url
        return str(self.app.url_path_for(endpoint_or_url, **kwargs))

    def load_css(self, css_url=None, version=DROPZONE_VERSION):
        """Load Dropzone's css resources."""
        url = css_url or f'https://cdn.jsdelivr.net/npm/dropzone@{version}/dist/min/dropzone.min.css'
        return Markup(f'<link rel="stylesheet" href="{url}" type="text/css">\n')

    def load_js(self, js_url=None, version=DROPZONE_VERSION):
        """Load Dropzone's js resources."""
        url = js_url or f'https://cdn.jsdelivr.net/npm/dropzone@{version}/dist/min/dropzone.min.js'
        return Markup(f'<script src="{url}"></script>\n')

    def load(self, js_url=None, css_url=None, version=DROPZONE_VERSION, **kwargs):
        """Load Dropzone's resources and initialize its configuration."""
        return Markup('%s%s%s' % (
            self.load_css(css_url, version),
            self.load_js(js_url, version),
            self.config(**kwargs),
        ))

    def config(self, redirect_url=None, custom_init='', custom_options='', id='myDropzone', **kwargs):
        """Initialize the dropzone configuration."""
        def _get_config(key):
            return kwargs.get(key, self.settings[f'DROPZONE_{key.upper()}'])

        if custom_init and not custom_init.strip().endswith(';'):
            custom_init += ';'
        if custom_options and not custom_options.strip().endswith(','):
            custom_options += ','

        upload_multiple = 'true' if _get_config('upload_multiple') in [True, 'true', 'True', 1] else 'false'
        redirect_view = _get_config('redirect_view')
        if redirect_view is not None or redirect_url is not None:
            redirect_url = redirect_url or self.get_url(redirect_view)
            redirect_js = '''
            this.on("queuecomplete", function(file) {
            // Called when all files in the queue finish uploading.
            window.location = "%s";
            });''' % redirect_url
        else:
            redirect_js = ''

        timeout = _get_config('timeout')
        if timeout:
            custom_options += 'timeout: %d,' % timeout

        allowed_type = (
            _get_config('allowed_file_type')
            if _get_config('allowed_file_custom')
            else ALLOWED_FILE_EXTENSIONS[_get_config('allowed_file_type')]
        )

        return Markup('''<script>
        Dropzone.options.%s = {
          init: function() {
              %s  // redirect after queue complete
              %s  // custom init code
          },
          uploadMultiple: %s,
          parallelUploads: %d,
          paramName: "%s", // The name that will be used to transfer the file
          maxFilesize: %d, // MB
          acceptedFiles: "%s",
          maxFiles: %s,
          dictDefaultMessage: `%s`, // message display on drop area
          dictFallbackMessage: "%s",
          dictInvalidFileType: "%s",
          dictFileTooBig: "%s",
          dictResponseError: "%s",
          dictMaxFilesExceeded: "%s",
          dictCancelUpload: "%s",
          dictRemoveFile: "%s",
          dictCancelUploadConfirmation: "%s",
          dictUploadCanceled: "%s",
          %s  // custom options code
        };
        </script>
                ''' % (
            id,
            redirect_js,
            custom_init,
            upload_multiple,
            _get_config('parallel_uploads'),
            _get_config('input_name'),
            _get_config('max_file_size'),
            allowed_type,
            _get_config('max_files'),
            _get_config('default_message'),
            _get_config('browser_unsupported'),
            _get_config('invalid_file_type'),
            _get_config('file_too_big'),
            _get_config('server_error'),
            _get_config('max_file_exceed'),
            _get_config('cancel_upload'),
            _get_config('remove_file'),
            _get_config('cancel_confirmation'),
            _get_config('upload_canceled'),
            custom_options,
        ))

    def create(self, action='', action_view='', id='myDropzone', **kwargs):
        """Create a Dropzone form with the given action."""
        if self.settings['DROPZONE_IN_FORM']:
            return Markup('<div class="dropzone" id="%s"></div>' % id)

        action_url = self.get_url(action or action_view, **kwargs)
        return Markup('''<form action="%s" method="post" class="dropzone" id="%s"
        enctype="multipart/form-data"></form>''' % (action_url, id))

    def style(self, css, id=None):
        """Add css to the dropzone element."""
        if id is not None:
            return Markup('<style>\n.dropzone#%s{%s}\n</style>' % (id, css))
        return Markup('<style>\n.dropzone{%s}\n</style>' % css)
