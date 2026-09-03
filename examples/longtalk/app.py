from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2.utils import generate_lorem_ipsum

from helpers import render_template

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()
app.state.config = {}
app.mount('/static', StaticFiles(directory=BASE_DIR / 'static', check_dir=False), name='static')


@app.get('/')
def index(request: Request):
    post_body = generate_lorem_ipsum(n=3)
    return render_template(request, 'index.html', post_body=post_body)


@app.get('/more', response_class=HTMLResponse)
def more():
    return generate_lorem_ipsum(n=3)
