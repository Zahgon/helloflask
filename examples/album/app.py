import os
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from wtforms import SubmitField
from wtforms.fields import FileField

from helpers import (
    BaseForm, FileAllowed, FileRequired, FileSize, create_form, flash, render_template,
    save_upload, send_from_directory, url_for,
)

BASE_DIR = Path(__file__).resolve().parent
SECRET_KEY = os.getenv('SECRET_KEY', 'secret string')

app = FastAPI()
app.state.config = config = {
    'SECRET_KEY': SECRET_KEY,
    'UPLOAD_PATH': BASE_DIR / 'uploads',
}
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount('/static', StaticFiles(directory=BASE_DIR / 'static', check_dir=False), name='static')


class UploadPhotoForm(BaseForm):
    photo = FileField('Upload Photo', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif']),
        FileSize(5 * 1024 * 1024)
    ])
    submit = SubmitField()


def random_filename(origin_filename):
    ext = Path(origin_filename).suffix
    new_filename = f'{uuid.uuid4().hex}{ext}'
    return new_filename


@app.get('/')
def index(request: Request):
    return render_template(request, 'index.html')


@app.get('/photos/{filename:path}')
def get_photo(filename: str):
    return send_from_directory(config['UPLOAD_PATH'], filename)


@app.api_route('/upload', methods=['GET', 'POST'])
async def upload(request: Request):
    form = await create_form(request, UploadPhotoForm)
    if form.validate_on_submit():
        photo = form.photo.data
        filename = random_filename(photo.filename)
        save_upload(photo, config['UPLOAD_PATH'] / filename)
        flash(request, 'Upload success.')
        request.session['photos'] = [filename]
        return RedirectResponse(url_for(request, 'index'), status_code=302)
    return render_template(request, 'upload.html', form=form)
