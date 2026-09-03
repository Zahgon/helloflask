"""FastAPI equivalents of the Flask helpers used by this example."""
import shutil
from pathlib import Path
from urllib.parse import urlencode, urljoin

from fastapi import HTTPException
from fastapi.responses import FileResponse
from fastapi.templating import Jinja2Templates
from jinja2 import pass_context
from starlette.datastructures import UploadFile
from wtforms import Form
from wtforms.csrf.session import SessionCSRF
from wtforms.validators import StopValidation

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=BASE_DIR / 'templates')


def url_for(request, endpoint, **values):
    """Build the URL of the given endpoint (equivalent to Flask's url_for())."""
    external = values.pop('_external', False)
    if endpoint == 'static':
        url = str(request.app.url_path_for('static', path=values.pop('filename')))
    else:
        candidates = [r for r in request.app.routes if getattr(r, 'name', None) == endpoint]
        route = max(
            (r for r in candidates if set(r.param_convertors) <= set(values)),
            key=lambda r: len(r.param_convertors),
            default=candidates[0],
        )
        path_params = {name: values.pop(name) for name in route.param_convertors}
        url = str(request.app.url_path_for(endpoint, **path_params))
    if values:
        url = f'{url}?{urlencode(values)}'
    if external:
        url = urljoin(str(request.base_url), url)
    return url


def flash(request, message):
    """Store a message to be shown on the next rendered page."""
    request.session.setdefault('_flashes', []).append(message)


def get_flashed_messages(request):
    """Pull the flashed messages out of the session."""
    return request.session.pop('_flashes', [])


def render_template(request, template_name, status_code=200, **context):
    """Render a template with the given context."""
    context['request'] = request
    context.setdefault('session', request.session)
    return templates.TemplateResponse(request, template_name, context, status_code=status_code)


def send_from_directory(directory, filename):
    """Serve a file stored in the given directory (Flask's send_from_directory())."""
    directory = Path(directory).resolve()
    path = (directory / filename).resolve()
    if directory not in path.parents or not path.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(path)


def save_upload(upload, destination):
    """Write an uploaded file to the given path (FileStorage.save() replacement)."""
    upload.file.seek(0)
    with open(destination, 'wb') as f:
        shutil.copyfileobj(upload.file, f)


def _is_uploaded(data):
    return isinstance(data, UploadFile) and bool(data.filename)


class FileRequired:
    """Validate that an actual file was uploaded."""

    def __init__(self, message=None):
        self.message = message

    def __call__(self, form, field):
        if not _is_uploaded(field.data):
            raise StopValidation(self.message or field.gettext('This field is required.'))


class FileAllowed:
    """Validate that the uploaded file has one of the given extensions."""

    def __init__(self, extensions, message=None):
        self.extensions = extensions
        self.message = message

    def __call__(self, form, field):
        if not _is_uploaded(field.data):
            return
        extension = Path(field.data.filename).suffix.lower().lstrip('.')
        if extension in self.extensions:
            return
        raise StopValidation(self.message or field.gettext(
            'File does not have an approved extension: %s' % ', '.join(self.extensions)
        ))


class FileSize:
    """Validate that the size of the uploaded file is within the given range."""

    def __init__(self, max_size, min_size=0, message=None):
        self.max_size = max_size
        self.min_size = min_size
        self.message = message

    def __call__(self, form, field):
        if not _is_uploaded(field.data):
            return
        field.data.file.seek(0, 2)
        size = field.data.file.tell()
        field.data.file.seek(0)
        if self.min_size <= size <= self.max_size:
            return
        raise StopValidation(self.message or field.gettext(
            'File must be between %d and %d bytes.' % (self.min_size, self.max_size)
        ))


class BaseForm(Form):
    """A session-backed CSRF protected form (replacement for FlaskForm)."""

    class Meta:
        csrf = True
        csrf_class = SessionCSRF

    is_submitted = False

    def validate_on_submit(self):
        return self.is_submitted and self.validate()


async def create_form(request, form_class, **kwargs):
    """Build a form from the submitted data (replacement for FlaskForm())."""
    is_submitted = request.method in ('POST', 'PUT', 'PATCH', 'DELETE')
    formdata = await request.form() if is_submitted else None
    config = request.app.state.config
    meta = {
        'csrf_context': request.session,
        'csrf_secret': config['SECRET_KEY'].encode(),
        'csrf': config.get('CSRF_ENABLED', True),
    }
    form = form_class(formdata, meta=meta, **kwargs)
    form.is_submitted = is_submitted
    return form


def validate_csrf(form):
    """Validate only the CSRF token of a submitted form."""
    field = getattr(form, form.meta.csrf_field_name, None)
    if field is None:  # CSRF protection is disabled
        return True
    return field.validate(form)


templates.env.globals['url_for'] = pass_context(
    lambda context, endpoint, **values: url_for(context['request'], endpoint, **values)
)
templates.env.globals['get_flashed_messages'] = pass_context(
    lambda context: get_flashed_messages(context['request'])
)
