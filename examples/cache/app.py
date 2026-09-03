import time
from pathlib import Path

from debug_toolbar.middleware import DebugToolbarMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from cache import Cache
from helpers import flash, render_template, url_for

BASE_DIR = Path(__file__).resolve().parent
SECRET_KEY = 'dev key'

app = FastAPI()
app.state.config = {
    'SECRET_KEY': SECRET_KEY,
    'CACHE_TYPE': 'SimpleCache',
}
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount('/static', StaticFiles(directory=BASE_DIR / 'static', check_dir=False), name='static')

cache = Cache(app)
# the redirects panel is disabled by default, like DEBUG_TB_INTERCEPT_REDIRECTS = False
app.add_middleware(DebugToolbarMiddleware)


@app.get('/')
def index(request: Request):
    return render_template(request, 'index.html')


@app.get('/foo')
def foo(request: Request):
    time.sleep(1)
    return render_template(request, 'foo.html')


@app.get('/bar')
@cache.cached(timeout=10 * 60)
def bar(request: Request):
    time.sleep(1)
    return render_template(request, 'bar.html')


@app.get('/baz')
@cache.cached(timeout=60 * 60)
def baz(request: Request):
    time.sleep(1)
    return render_template(request, 'baz.html')


@app.get('/qux')
@cache.cached(query_string=True)
def qux(request: Request):
    time.sleep(1)
    page = request.query_params.get('page', 1)
    return render_template(request, 'qux.html', page=page)


@app.get('/update/bar')
def update_bar(request: Request):
    cache.delete('view/%s' % url_for(request, 'bar'))
    flash(request, 'Cached data for bar have been deleted.')
    return RedirectResponse(url_for(request, 'index'), status_code=302)


@app.get('/update/baz')
def update_baz(request: Request):
    cache.delete('view/%s' % url_for(request, 'baz'))
    flash(request, 'Cached data for baz have been deleted.')
    return RedirectResponse(url_for(request, 'index'), status_code=302)


@app.get('/update/all')
def update_all(request: Request):
    cache.clear()
    flash(request, 'All cached data deleted.')
    return RedirectResponse(url_for(request, 'index'), status_code=302)


# cache other function
@cache.cached(key_prefix='add')
def add(a, b):
    time.sleep(2)
    return a + b


# cache memorize (with argument)
@cache.memoize()
def add_pro(a, b):
    time.sleep(2)
    return a + b


def del_add_cache():
    cache.delete('add')


# delete memorized cache
def del_pro_cache():
    cache.delete_memoized(add_pro)
