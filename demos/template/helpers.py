"""FastAPI equivalents of the Flask helpers used by this example."""
from pathlib import Path
from urllib.parse import urlencode, urljoin

from fastapi.templating import Jinja2Templates
from jinja2 import pass_context

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(directory=BASE_DIR / 'templates')

context_processors = []


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


def context_processor(func):
    """Register a template context processor."""
    context_processors.append(func)
    return func


def template_global(name=None):
    """Register a template global function."""
    def decorator(func):
        templates.env.globals[name or func.__name__] = func
        return func
    return decorator


def template_filter(name=None):
    """Register a template filter."""
    def decorator(func):
        templates.env.filters[name or func.__name__] = func
        return func
    return decorator


def template_test(name=None):
    """Register a template test."""
    def decorator(func):
        templates.env.tests[name or func.__name__] = func
        return func
    return decorator


def render_template(request, template_name, status_code=200, **context):
    """Render a template with the given context."""
    for processor in context_processors:
        context.update(processor())
    context['request'] = request
    return templates.TemplateResponse(request, template_name, context, status_code=status_code)


templates.env.globals['url_for'] = pass_context(
    lambda context, endpoint, **values: url_for(context['request'], endpoint, **values)
)
templates.env.globals['get_flashed_messages'] = pass_context(
    lambda context: get_flashed_messages(context['request'])
)
