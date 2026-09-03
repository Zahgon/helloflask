# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li
    :license: MIT, see LICENSE for more details.
"""
import click
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()
app.state.config = {}


# the minimal FastAPI application
@app.get('/', response_class=HTMLResponse)
def index():
    return '<h1>Hello, World!</h1>'


# bind multiple URL for one view function
@app.get('/hi', response_class=HTMLResponse)
@app.get('/hello', response_class=HTMLResponse)
def say_hello():
    return '<h1>Hello, Flask!</h1>'


# dynamic route, URL variable default
@app.get('/greet', response_class=HTMLResponse)
@app.get('/greet/{name}', response_class=HTMLResponse)
def greet(name: str = 'Programmer'):
    return '<h1>Hello, %s!</h1>' % name


# custom cli command
@click.group()
def cli():
    """Manage the application."""


@cli.command()
def hello():
    """Just say hello."""
    click.echo('Hello, Human!')


if __name__ == '__main__':
    cli()
