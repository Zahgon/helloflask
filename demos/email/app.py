# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li
    :license: MIT, see LICENSE for more details.
"""
import os
from pathlib import Path
from threading import Thread

import sendgrid
from sendgrid.helpers.mail import Email as SGEmail, Content, Mail as SGMail
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from wtforms import StringField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email

from helpers import (
    BaseForm, create_form, flash, render_template, render_to_string, templates, url_for,
)
from mail import Mail, Message

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()
app.state.config = config = {}
app.mount('/static', StaticFiles(directory=BASE_DIR / 'static', check_dir=False), name='static')
templates.env.trim_blocks = True
templates.env.lstrip_blocks = True

config.update(
    SECRET_KEY=os.getenv('SECRET_KEY', 'secret string'),
    MAIL_SERVER=os.getenv('MAIL_SERVER'),
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME=os.getenv('MAIL_USERNAME'),
    MAIL_PASSWORD=os.getenv('MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER=('Grey Li', os.getenv('MAIL_USERNAME'))
)
app.add_middleware(SessionMiddleware, secret_key=config['SECRET_KEY'])

mail = Mail(app)


# send over SMTP
def send_smtp_mail(subject, to, body):
    message = Message(subject, recipients=[to], body=body)
    mail.send(message)


# send over SendGrid Web API
def send_api_mail(subject, to, body):
    sg = sendgrid.SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))
    from_email = SGEmail('Grey Li <noreply@helloflask.com>')
    to_email = SGEmail(to)
    content = Content("text/plain", body)
    email = SGMail(from_email, subject, to_email, content)
    sg.client.mail.send.post(request_body=email.get())


# send email asynchronously
def _send_async_mail(message):
    mail.send(message)


def send_async_mail(subject, to, body):
    message = Message(subject, recipients=[to], body=body)
    thr = Thread(target=_send_async_mail, args=[message])
    thr.start()
    return thr


# send email with HTML body
def send_subscribe_mail(request, subject, to, **kwargs):
    message = Message(subject, recipients=[to], sender='Flask Weekly <%s>' % os.getenv('MAIL_USERNAME'))
    message.body = render_to_string(request, 'emails/subscribe.txt', **kwargs)
    message.html = render_to_string(request, 'emails/subscribe.html', **kwargs)
    mail.send(message)


class EmailForm(BaseForm):
    to = StringField('To', validators=[DataRequired(), Email()])
    subject = StringField('Subject', validators=[DataRequired()])
    body = TextAreaField('Body', validators=[DataRequired()])
    submit_smtp = SubmitField('Send with SMTP')
    submit_api = SubmitField('Send with SendGrid API')
    submit_async = SubmitField('Send with SMTP asynchronously')


class SubscribeForm(BaseForm):
    name = StringField('Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Subscribe')


@app.api_route('/', methods=['GET', 'POST'])
async def index(request: Request):
    form = await create_form(request, EmailForm)
    if form.validate_on_submit():
        to = form.to.data
        subject = form.subject.data
        body = form.body.data
        formdata = await request.form()
        if form.submit_smtp.data:
            send_smtp_mail(subject, to, body)
            method = formdata.get('submit_smtp')
        elif form.submit_api.data:
            send_api_mail(subject, to, body)
            method = formdata.get('submit_api')
        else:
            send_async_mail(subject, to, body)
            method = formdata.get('submit_async')

        flash(request, 'Email sent %s! Check your inbox.' % ' '.join(method.split()[1:]))
        return RedirectResponse(url_for(request, 'index'), status_code=302)
    form.subject.data = 'Hello, World!'
    form.body.data = 'Across the Great Wall we can reach every corner in the world.'
    return render_template(request, 'index.html', form=form)


@app.api_route('/subscribe', methods=['GET', 'POST'])
async def subscribe(request: Request):
    form = await create_form(request, SubscribeForm)
    if form.validate_on_submit():
        name = form.name.data
        email = form.email.data
        send_subscribe_mail(request, 'Subscribe Success!', email, name=name)
        flash(request, 'Confirmation email have been sent! Check your inbox.')
        return RedirectResponse(url_for(request, 'subscribe'), status_code=302)
    return render_template(request, 'subscribe.html', form=form)


@app.get('/unsubscribe')
def unsubscribe(request: Request):
    flash(request, 'Want to unsubscribe? No way...')
    return RedirectResponse(url_for(request, 'subscribe'), status_code=302)
