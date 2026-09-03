"""FastAPI equivalents of the Flask helpers used by this example."""
from pathlib import Path
from urllib.parse import urlencode, urljoin

from fastapi.templating import Jinja2Templates
from jinja2 import pass_context
from wtforms import Form
from wtforms.csrf.session import SessionCSRF

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
    return templates.TemplateResponse(request, template_name, context, status_code=status_code)


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


templates.env.globals['url_for'] = pass_context(
    lambda context, endpoint, **values: url_for(context['request'], endpoint, **values)
)
templates.env.globals['get_flashed_messages'] = pass_context(
    lambda context: get_flashed_messages(context['request'])
)


def render_to_string(request, template_name, **context):
    """Render a template to a string (used for the email bodies)."""
    context['request'] = request
    return templates.get_template(template_name).render(context)
