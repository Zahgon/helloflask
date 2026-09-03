import click
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

app = FastAPI()
app.state.config = {}


@app.get('/', response_class=HTMLResponse)
def index():
    return '<h1>Hello, world!</h1>'


@app.get('/ping', response_class=HTMLResponse)
@app.get('/pong', response_class=HTMLResponse)
def hello_flask():
    return '<h1>Hello, Flask!</h1>'


@app.get('/greet', response_class=HTMLResponse)  # 为 name 变量设定一个默认值
@app.get('/greet/{name}', response_class=HTMLResponse)
def greet(name: str = 'Programmer'):
    return f'<h1>Hello, {name}!</h1>'


# 命令组 $ python app.py hello
@click.group()
def cli():
    """Manage the application."""


@cli.command()
def hello():
    """Just say hello."""
    click.echo('Hello, Human!')


if __name__ == '__main__':
    cli()
