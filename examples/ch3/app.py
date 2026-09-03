import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from markupsafe import Markup
from starlette.middleware.sessions import SessionMiddleware

from helpers import (
    context_processor, flash, render_template, template_filter, template_global,
    template_test, url_for,
)

SECRET_KEY = os.getenv('SECRET_KEY', 'secret string')

app = FastAPI()
app.state.config = {'SECRET_KEY': SECRET_KEY}
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount(
    '/static',
    StaticFiles(directory=Path(__file__).resolve().parent / 'static', check_dir=False),
    name='static',
)

user = {
    'username': 'Grey Li',
    'bio': 'A boy who loves movies and music.',
}

movies = [
    {'name': 'My Neighbor Totoro', 'year': '1988'},
    {'name': 'Three Colours trilogy', 'year': '1993'},
    {'name': 'Forrest Gump', 'year': '1994'},
    {'name': 'Perfect Blue', 'year': '1997'},
    {'name': 'The Matrix', 'year': '1999'},
    {'name': 'Memento', 'year': '2000'},
    {'name': 'The Bucket list', 'year': '2007'},
    {'name': 'Black Swan', 'year': '2010'},
    {'name': 'Gone Girl', 'year': '2014'},
    {'name': 'CoCo', 'year': '2017'},
]


@app.get('/watchlist')
def watchlist(request: Request):
    return render_template(request, 'watchlist.html', user=user, movies=movies)


@app.get('/')
def index(request: Request):
    return render_template(request, 'index.html')


# register template context handler
@context_processor
def inject_info():
    foo = 'I am foo.'
    return dict(foo=foo)  # equal to: return {'foo': foo}


# register template global function
@template_global()
def bar():
    return 'I am bar.'


# register template filter
@template_filter()
def musical(s):
    return s + Markup(' &#9835;')


# register template test
@template_test()
def baz(n):
    if n == 'baz':
        return True
    return False


@app.get('/watchlist2')
def watchlist_with_static(request: Request):
    return render_template(request, 'watchlist_with_static.html', user=user, movies=movies)


# message flashing
@app.get('/flash')
def call_flash(request: Request):
    flash(request, 'This is Flash speaking, who is calling?')
    return RedirectResponse(url_for(request, 'index'), status_code=302)


# 404 error handler
@app.exception_handler(404)
def page_not_found(request: Request, exc):
    return render_template(request, 'errors/404.html', status_code=404)


# 500 error handler
@app.exception_handler(500)
def internal_server_error(request: Request, exc):
    return render_template(request, 'errors/500.html', status_code=500)
