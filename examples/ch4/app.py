import os
import uuid
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from wtforms import ValidationError

from forms import LoginForm, FortyTwoForm
from helpers import create_form, flash, render_template, url_for

SECRET_KEY = os.getenv('SECRET_KEY', 'secret string')

app = FastAPI()
app.state.config = {'SECRET_KEY': SECRET_KEY}
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount(
    '/static',
    StaticFiles(directory=Path(__file__).resolve().parent / 'static', check_dir=False),
    name='static',
)


@app.api_route('/', methods=['GET', 'POST'])
def index(request: Request):
    return render_template(request, 'index.html')


@app.api_route('/html', methods=['GET', 'POST'])
async def html(request: Request):
    form = await create_form(request, LoginForm)
    if request.method == 'POST':
        username = (await request.form()).get('username')
        flash(request, f'Welcome home, {username}!')
        return RedirectResponse(url_for(request, 'index'), status_code=302)
    return render_template(request, 'pure_html.html')


@app.api_route('/basic', methods=['GET', 'POST'])
async def basic(request: Request):
    form = await create_form(request, LoginForm)
    if form.validate_on_submit():
        username = form.username.data
        flash(request, f'Welcome home, {username}!')
        return RedirectResponse(url_for(request, 'index'), status_code=302)
    return render_template(request, 'basic.html', form=form)


@app.api_route('/bootstrap', methods=['GET', 'POST'])
async def bootstrap(request: Request):
    form = await create_form(request, LoginForm)
    if form.validate_on_submit():
        username = form.username.data
        flash(request, f'Welcome home, {username}!')
        return RedirectResponse(url_for(request, 'index'), status_code=302)
    return render_template(request, 'bootstrap.html', form=form)


@app.api_route('/custom-validator', methods=['GET', 'POST'])
async def custom_validator(request: Request):
    form = await create_form(request, FortyTwoForm)
    if form.validate_on_submit():
        flash(request, 'Bingo!')
        return RedirectResponse(url_for(request, 'index'), status_code=302)
    return render_template(request, 'custom_validator.html', form=form)
