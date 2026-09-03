# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li
    :license: MIT, see LICENSE for more details.
"""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from webassets import Bundle, Environment
from webassets.ext.jinja2 import AssetsExtension

from ckeditor import CKEditor
from helpers import render_template, templates

BASE_DIR = Path(__file__).resolve().parent
SECRET_KEY = 'dev key'

app = FastAPI()
app.state.config = {'SECRET_KEY': SECRET_KEY}
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount('/static', StaticFiles(directory=BASE_DIR / 'static', check_dir=False), name='static')
templates.env.trim_blocks = True
templates.env.lstrip_blocks = True

assets = Environment(directory=BASE_DIR / 'static', url='/static')
templates.env.add_extension(AssetsExtension)
templates.env.assets_environment = assets

ckeditor = CKEditor(app, templates)

css = Bundle('css/bootstrap.min.css',
             'css/bootstrap.css',
             'css/dropzone.min.css',
             'css/jquery.Jcrop.min.css',
             'css/style.css',
             filters='cssmin', output='gen/packed.css')

js = Bundle('js/jquery.min.js',
            'js/popper.min.js',
            'js/bootstrap.min.js',
            'js/bootstrap.js',
            'js/moment-with-locales.min.js',
            'js/dropzone.min.js',
            'js/jquery.Jcrop.min.js',
            filters='jsmin', output='gen/packed.js')

assets.register('js_all', js)
assets.register('css_all', css)


@app.get('/')
def index(request: Request):
    return render_template(request, 'index.html')


@app.get('/foo')
def unoptimized(request: Request):
    return render_template(request, 'unoptimized.html')


@app.get('/bar')
def optimized(request: Request):
    return render_template(request, 'optimized.html')
