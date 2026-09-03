# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li
    :license: MIT, see LICENSE for more details.
"""
import os
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from ckeditor import CKEditor, upload_success, upload_fail
from dropzone import Dropzone
from forms import LoginForm, FortyTwoForm, NewPostForm, UploadForm, MultiUploadForm, SigninForm, \
    RegisterForm, SigninForm2, RegisterForm2, RichTextForm
from helpers import (
    create_form, flash, render_template, save_upload, send_from_directory, templates,
    url_for, validate_csrf,
)

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()
app.state.config = config = {'SECRET_KEY': os.getenv('SECRET_KEY', 'secret string')}
app.add_middleware(SessionMiddleware, secret_key=config['SECRET_KEY'])
app.mount('/static', StaticFiles(directory=BASE_DIR / 'static', check_dir=False), name='static')
templates.env.trim_blocks = True
templates.env.lstrip_blocks = True

# Custom config
config['UPLOAD_PATH'] = os.path.join(BASE_DIR, 'uploads')

if not os.path.exists(config['UPLOAD_PATH']):
    os.makedirs(config['UPLOAD_PATH'])

config['ALLOWED_EXTENSIONS'] = ['png', 'jpg', 'jpeg', 'gif']

# Request body size
# Starlette has no MAX_CONTENT_LENGTH equivalent: limit the request body size
# in the ASGI server or in the reverse proxy in front of it.

# CKEditor config
# the local copy of CKEditor used to be shipped with Flask-CKEditor, it is loaded from the CDN now
config['CKEDITOR_FILE_UPLOADER'] = 'upload_for_ckeditor'

# Dropzone config
config['DROPZONE_ALLOWED_FILE_TYPE'] = 'image'
config['DROPZONE_MAX_FILE_SIZE'] = 3
config['DROPZONE_MAX_FILES'] = 30

ckeditor = CKEditor(app, templates)
dropzone = Dropzone(app, templates)


@app.api_route('/', methods=['GET', 'POST'])
def index(request: Request):
    return render_template(request, 'index.html')


@app.api_route('/html', methods=['GET', 'POST'])
async def html(request: Request):
    form = await create_form(request, LoginForm)
    if request.method == 'POST':
        username = (await request.form()).get('username')
        flash(request, 'Welcome home, %s!' % username)
        return RedirectResponse(url_for(request, 'index'), status_code=302)
    return render_template(request, 'pure_html.html')


@app.api_route('/basic', methods=['GET', 'POST'])
async def basic(request: Request):
    form = await create_form(request, LoginForm)
    if form.validate_on_submit():
        username = form.username.data
        flash(request, 'Welcome home, %s!' % username)
        return RedirectResponse(url_for(request, 'index'), status_code=302)
    return render_template(request, 'basic.html', form=form)


@app.api_route('/bootstrap', methods=['GET', 'POST'])
async def bootstrap(request: Request):
    form = await create_form(request, LoginForm)
    if form.validate_on_submit():
        username = form.username.data
        flash(request, 'Welcome home, %s!' % username)
        return RedirectResponse(url_for(request, 'index'), status_code=302)
    return render_template(request, 'bootstrap.html', form=form)


@app.api_route('/custom-validator', methods=['GET', 'POST'])
async def custom_validator(request: Request):
    form = await create_form(request, FortyTwoForm)
    if form.validate_on_submit():
        flash(request, 'Bingo!')
        return RedirectResponse(url_for(request, 'index'), status_code=302)
    return render_template(request, 'custom_validator.html', form=form)


@app.get('/uploads/{filename:path}')
def get_file(filename: str):
    return send_from_directory(config['UPLOAD_PATH'], filename)


@app.get('/uploaded-images')
def show_images(request: Request):
    return render_template(request, 'uploaded.html')


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config['ALLOWED_EXTENSIONS']


def random_filename(filename):
    ext = os.path.splitext(filename)[1]
    new_filename = uuid.uuid4().hex + ext
    return new_filename


@app.api_route('/upload', methods=['GET', 'POST'])
async def upload(request: Request):
    form = await create_form(request, UploadForm)
    if form.validate_on_submit():
        f = form.photo.data
        filename = random_filename(f.filename)
        save_upload(f, os.path.join(config['UPLOAD_PATH'], filename))
        flash(request, 'Upload success.')
        request.session['filenames'] = [filename]
        return RedirectResponse(url_for(request, 'show_images'), status_code=302)
    return render_template(request, 'upload.html', form=form)


@app.api_route('/multi-upload', methods=['GET', 'POST'])
async def multi_upload(request: Request):
    form = await create_form(request, MultiUploadForm)

    if request.method == 'POST':
        filenames = []

        # check csrf token
        if not validate_csrf(form):
            flash(request, 'CSRF token error.')
            return RedirectResponse(url_for(request, 'multi_upload'), status_code=302)

        photos = (await request.form()).getlist('photo')
        # check if user has selected files. If not, the browser
        # will submit an empty file part without filename
        if not photos[0].filename:
            flash(request, 'No selected file.')
            return RedirectResponse(url_for(request, 'multi_upload'), status_code=302)

        for f in photos:
            # check the file extension
            if f and allowed_file(f.filename):
                filename = random_filename(f.filename)
                save_upload(f, os.path.join(
                    config['UPLOAD_PATH'], filename
                ))
                filenames.append(filename)
            else:
                flash(request, 'Invalid file type.')
                return RedirectResponse(url_for(request, 'multi_upload'), status_code=302)
        flash(request, 'Upload success.')
        request.session['filenames'] = filenames
        return RedirectResponse(url_for(request, 'show_images'), status_code=302)
    return render_template(request, 'upload.html', form=form)


@app.api_route('/dropzone-upload', methods=['GET', 'POST'])
async def dropzone_upload(request: Request):
    if request.method == 'POST':
        formdata = await request.form()
        # check if the post request has the file part
        if 'file' not in formdata:
            return Response('This field is required.', status_code=400)
        f = formdata.get('file')

        if f and allowed_file(f.filename):
            filename = random_filename(f.filename)
            save_upload(f, os.path.join(
                config['UPLOAD_PATH'], filename
            ))
        else:
            return Response('Invalid file type.', status_code=400)
    return render_template(request, 'dropzone.html')


@app.api_route('/two-submits', methods=['GET', 'POST'])
async def two_submits(request: Request):
    form = await create_form(request, NewPostForm)
    if form.validate_on_submit():
        if form.save.data:
            # save it...
            flash(request, 'You click the "Save" button.')
        elif form.publish.data:
            # publish it...
            flash(request, 'You click the "Publish" button.')
        return RedirectResponse(url_for(request, 'index'), status_code=302)
    return render_template(request, '2submit.html', form=form)


@app.api_route('/multi-form', methods=['GET', 'POST'])
async def multi_form(request: Request):
    signin_form = await create_form(request, SigninForm)
    register_form = await create_form(request, RegisterForm)

    if signin_form.submit1.data and signin_form.validate():
        username = signin_form.username.data
        flash(request, '%s, you just submit the Signin Form.' % username)
        return RedirectResponse(url_for(request, 'index'), status_code=302)

    if register_form.submit2.data and register_form.validate():
        username = register_form.username.data
        flash(request, '%s, you just submit the Register Form.' % username)
        return RedirectResponse(url_for(request, 'index'), status_code=302)

    return render_template(request, '2form.html', signin_form=signin_form, register_form=register_form)


@app.get('/multi-form-multi-view')
async def multi_form_multi_view(request: Request):
    signin_form = await create_form(request, SigninForm2)
    register_form = await create_form(request, RegisterForm2)
    return render_template(request, '2form2view.html', signin_form=signin_form, register_form=register_form)


@app.post('/handle-signin')
async def handle_signin(request: Request):
    signin_form = await create_form(request, SigninForm2)
    register_form = await create_form(request, RegisterForm2)

    if signin_form.validate_on_submit():
        username = signin_form.username.data
        flash(request, '%s, you just submit the Signin Form.' % username)
        return RedirectResponse(url_for(request, 'index'), status_code=302)

    return render_template(request, '2form2view.html', signin_form=signin_form, register_form=register_form)


@app.post('/handle-register')
async def handle_register(request: Request):
    signin_form = await create_form(request, SigninForm2)
    register_form = await create_form(request, RegisterForm2)

    if register_form.validate_on_submit():
        username = register_form.username.data
        flash(request, '%s, you just submit the Register Form.' % username)
        return RedirectResponse(url_for(request, 'index'), status_code=302)
    return render_template(request, '2form2view.html', signin_form=signin_form, register_form=register_form)


@app.api_route('/ckeditor', methods=['GET', 'POST'])
async def integrate_ckeditor(request: Request):
    form = await create_form(request, RichTextForm)
    if form.validate_on_submit():
        title = form.title.data
        body = form.body.data
        flash(request, 'Your post is published!')
        return render_template(request, 'post.html', title=title, body=body)
    return render_template(request, 'ckeditor.html', form=form)


# handle image upload for ckeditor
@app.post('/upload-ck')
async def upload_for_ckeditor(request: Request):
    f = (await request.form()).get('upload')
    if not allowed_file(f.filename):
        return upload_fail('Image only!')
    save_upload(f, os.path.join(config['UPLOAD_PATH'], f.filename))
    url = url_for(request, 'get_file', filename=f.filename)
    return upload_success(url, f.filename)
