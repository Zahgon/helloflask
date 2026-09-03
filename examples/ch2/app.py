import os
from urllib.parse import urlparse, urljoin, urlencode

from markupsafe import escape
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from starlette.convertors import Convertor, register_url_convertor
from starlette.middleware.sessions import SessionMiddleware

SECRET_KEY = os.getenv('SECRET_KEY', 'secret string')

app = FastAPI()
app.state.config = {'SECRET_KEY': SECRET_KEY}
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


def url_for(request, endpoint, **values):
    """Build the URL of the given endpoint (equivalent to Flask's url_for())."""
    external = values.pop('_external', False)
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


# any URL converter
class AnyConvertor(Convertor):
    regex = 'blue|white|red'

    def convert(self, value: str) -> str:
        return value

    def to_string(self, value: str) -> str:
        return value


register_url_convertor('any_blue_white_red', AnyConvertor())


# get name value from query string and cookie
@app.get('/', response_class=HTMLResponse)
@app.get('/hello', response_class=HTMLResponse)
def hello(request: Request):
    name = request.query_params.get('name')
    if name is None:
        name = request.cookies.get('name', 'Human')
    response = f'<h1>Hello, {escape(name)}!</h1>'  # escape name to avoid XSS
    # return different response according to the user's authentication status
    if 'logged_in' in request.session:
        response += '[Authenticated]'
    else:
        response += '[Not Authenticated]'
    return response


# redirect
@app.get('/hi')
def hi(request: Request):
    return RedirectResponse(url_for(request, 'hello'), status_code=302)


# use int URL converter
@app.get('/back/{year:int}', response_class=HTMLResponse)
def time_machine(year: int):
    return f'Welcome to {2024 - year}!'


# use any URL converter
@app.get('/colors/{color:any_blue_white_red}', response_class=HTMLResponse)
def three_colors(color: str):
    return '<p>Love is patient and kind. Love is not jealous or boastful or proud or rude.</p>'


# return error response
@app.get('/brew/{drink}', response_class=HTMLResponse)
def teapot(drink: str):
    if drink == 'coffee':
        raise HTTPException(status_code=418)
    else:
        return 'A drop of tea.'


# 404
@app.get('/answer')
def the_answer():
    raise HTTPException(status_code=404)


# return response with different formats
@app.get('/note', response_class=Response)
@app.get('/note/{content_type}', response_class=Response)
def note(content_type: str = 'text'):
    content_type = content_type.lower()
    if content_type == 'text':
        body = '''Note
to: Morty
from: Rick
heading: Reminder
body: Don't Look Back
'''
        response = Response(content=body, media_type='text/plain')
    elif content_type == 'html':
        body = '''<!DOCTYPE html>
<html>
<head></head>
<body>
  <h1>Note</h1>
  <p>to: Morty</p>
  <p>from: Rick</p>
  <p>heading: Reminder</p>
  <p>body: <strong>Don't Look Back</strong></p>
</body>
</html>
'''
        response = Response(content=body, media_type='text/html')
    elif content_type == 'xml':
        body = '''<?xml version="1.0" encoding="UTF-8"?>
<note>
  <to>Morty</to>
  <from>Rick</from>
  <heading>Reminder</heading>
  <body>Don't Look Back</body>
</note>
'''
        response = Response(content=body, media_type='application/xml')
    elif content_type == 'json':
        body = {
            "note": {
                "to": "Morty",
                "from": "Rick",
                "heading": "Reminder",
                "body": "Don't Look Back"
            }
        }
        response = JSONResponse(body)
        # equal to:
        # response = Response(content=json.dumps(body), media_type="application/json")
    else:
        raise HTTPException(status_code=400)
    return response


# set cookie
@app.get('/set/{name}')
def set_cookie(request: Request, name: str):
    response = RedirectResponse(url_for(request, 'hello'), status_code=302)
    response.set_cookie('name', name)
    return response


# log in user
@app.get('/login')
def login(request: Request):
    request.session['logged_in'] = True
    return RedirectResponse(url_for(request, 'hello'), status_code=302)


# protect view
@app.get('/admin', response_class=HTMLResponse)
def admin(request: Request):
    if 'logged_in' not in request.session:
        raise HTTPException(status_code=403)
    return 'Welcome to admin page.'


# log out user
@app.get('/logout')
def logout(request: Request):
    if 'logged_in' in request.session:
        request.session.pop('logged_in')
    return RedirectResponse(url_for(request, 'hello'), status_code=302)


# redirect to last page
@app.get('/foo', response_class=HTMLResponse)
def foo(request: Request):
    url = url_for(request, 'do_something', next=full_path(request))
    return f'<h1>Foo page</h1><a href="{url}">Do something and redirect</a>'


@app.get('/bar', response_class=HTMLResponse)
def bar(request: Request):
    url = url_for(request, 'do_something', next=full_path(request))
    return f'<h1>Bar page</h1><a href="{url}">Do something and redirect</a>'


@app.get('/do-something')
def do_something(request: Request):
    # do something here
    return redirect_back(request)


def full_path(request):
    return f'{request.url.path}?{request.url.query}'


def is_safe_url(request, target):
    ref_url = urlparse(str(request.base_url))
    test_url = urlparse(urljoin(str(request.base_url), target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


def redirect_back(request, default='hello', **kwargs):
    for target in [request.query_params.get('next'), request.headers.get('referer')]:
        if not target:
            continue
        if is_safe_url(request, target):
            return RedirectResponse(target, status_code=302)
    return RedirectResponse(url_for(request, default, **kwargs), status_code=302)
