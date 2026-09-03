import os
import uuid
from pathlib import Path

from bleach import clean
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length

from ckeditor import CKEditor, CKEditorField, upload_fail, upload_success
from helpers import (
    BaseForm, create_form, flash, render_template, save_upload, send_from_directory,
    templates, url_for,
)

BASE_DIR = Path(__file__).resolve().parent
SECRET_KEY = os.getenv('SECRET_KEY', 'secret string')

app = FastAPI()
app.state.config = config = {
    'SECRET_KEY': SECRET_KEY,
    'CKEDITOR_FILE_UPLOADER': 'upload_image',
    'UPLOAD_PATH': BASE_DIR / 'uploads',
}
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount('/static', StaticFiles(directory=BASE_DIR / 'static', check_dir=False), name='static')

ckeditor = CKEditor(app, templates)


class ArticleForm(BaseForm):
    title = StringField('Title', validators=[DataRequired(), Length(1, 50)])
    body = CKEditorField('Body', validators=[DataRequired()])
    submit = SubmitField('Publish')


def clean_html(html):
    allowed_tags = ['a', 'abbr', 'b', 'br', 'blockquote', 'code',
                    'del', 'div', 'em', 'img', 'p', 'pre', 'strong',
                    'span', 'ul', 'li', 'ol']
    allowed_attributes = ['src', 'title', 'alt', 'href', 'class']
    return clean(html, tags=allowed_tags, attributes=allowed_attributes)


def allowed_file(filename):
    extension = Path(filename).suffix.lower()
    return '.' in filename and extension in ['.jpg', '.gif', '.png', '.jpeg']


def random_filename(old_filename):
    ext = Path(old_filename).suffix
    new_filename = uuid.uuid4().hex + ext
    return new_filename


@app.api_route('/', methods=['GET', 'POST'])
async def index(request: Request):
    form = await create_form(request, ArticleForm)
    if form.validate_on_submit():
        title = form.title.data
        body = clean_html(form.body.data)
        flash(request, 'Your article is published!')
        return render_template(request, 'article.html', title=title, body=body)
    return render_template(request, 'index.html', form=form)


@app.get('/uploads/{filename:path}')
def get_image(filename: str):
    return send_from_directory(config['UPLOAD_PATH'], filename)


@app.post('/upload')
async def upload_image(request: Request):
    f = (await request.form()).get('upload')
    if not allowed_file(f.filename):
        return upload_fail('Image only!')
    filename = random_filename(f.filename)
    save_upload(f, config['UPLOAD_PATH'] / filename)
    image_url = url_for(request, 'get_image', filename=filename)
    return upload_success(image_url, filename)
