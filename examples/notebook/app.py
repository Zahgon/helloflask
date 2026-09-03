import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from faker import Faker
from fastapi import Depends, FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, String, Text, MetaData, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.middleware.sessions import SessionMiddleware
from wtforms import SubmitField, StringField, TextAreaField
from wtforms.validators import DataRequired, Length

from helpers import BaseForm, create_form, flash, render_template, url_for

SQLITE_PREFIX = 'sqlite:///' if sys.platform.startswith('win') else 'sqlite:////'
SQLITE_PATH = Path(__file__).resolve().parent / 'data.db'
BASE_DIR = Path(__file__).resolve().parent
SECRET_KEY = os.getenv('SECRET_KEY', 'secret string')


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention={
        'ix': 'ix_%(column_0_label)s',
        'uq': 'uq_%(table_name)s_%(column_0_name)s',
        'ck': 'ck_%(table_name)s_%(constraint_name)s',
        'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
        'pk': 'pk_%(table_name)s'
    })


def create_db_engine(url):
    """Create the database engine with SQLite friendly defaults."""
    options = {}
    if url.startswith('sqlite'):
        options['connect_args'] = {'check_same_thread': False}
        if ':memory:' in url or url.endswith('sqlite://'):
            options['poolclass'] = StaticPool
    return create_engine(url, **options)


app = FastAPI()
app.state.config = config = {
    'SECRET_KEY': SECRET_KEY,
    'SQLALCHEMY_DATABASE_URI': os.getenv('DATABASE_URL', SQLITE_PREFIX + str(SQLITE_PATH)),
}
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.mount('/static', StaticFiles(directory=BASE_DIR / 'static', check_dir=False), name='static')

engine = create_db_engine(config['SQLALCHEMY_DATABASE_URI'])
Session = sessionmaker(bind=engine)


def get_session():
    """Provide a database session for the duration of the request."""
    with Session() as session:
        yield session


# models
class Note(Base):
    __tablename__ = 'note'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(50))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=datetime.now)

    def __repr__(self):
        return f'<Note {self.id}: {self.title}>'  # pragma: no cover


# commands
@click.group()
def cli():
    """Manage the application."""


@cli.command('init')
@click.option('--drop-table', is_flag=True, help='Re-create the tables.')
def init_command(drop_table):
    """Initialize the application."""
    if drop_table:
        click.confirm(
            'This operation will delete the tables, do you want to continue?',
            abort=True
        )
        Base.metadata.drop_all(engine)
        click.echo('Dropped tables.')
    Base.metadata.create_all(engine)
    click.echo('Initialized.')


@cli.command('lorem')
@click.option('--count', default=20, help='Quantity of notes, default is 20.')
def lorem_command(count):
    """Generate fake data."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    fake = Faker()

    with Session() as session:
        for _ in range(count):
            note = Note(
                title=fake.sentence(5),
                body=fake.text(200),
                created_at=fake.date_time_this_year(),
            )
            session.add(note)

        session.commit()
    click.echo(f'Created {count} notes.')


# forms
class NoteForm(BaseForm):
    title = StringField('Title', validators=[DataRequired(), Length(1, 50)])
    body = TextAreaField('Body', validators=[DataRequired()])
    submit = SubmitField()


class DeleteNoteForm(BaseForm):
    submit = SubmitField('Delete')


# views
@app.get('/')
async def index(request: Request, db_session=Depends(get_session)):
    notes = db_session.scalars(select(Note)).all()
    delete_form = await create_form(request, DeleteNoteForm)
    return render_template(request, 'index.html', notes=notes, delete_form=delete_form)


@app.api_route('/new', methods=['GET', 'POST'])
async def new_note(request: Request, db_session=Depends(get_session)):
    form = await create_form(request, NoteForm)
    if form.validate_on_submit():
        title = form.title.data
        body = form.body.data
        note = Note(title=title, body=body)
        db_session.add(note)
        db_session.commit()
        flash(request, 'Note saved.')
        return RedirectResponse(url_for(request, 'index'), status_code=302)
    return render_template(request, 'new_note.html', form=form)


@app.api_route('/edit/{note_id:int}', methods=['GET', 'POST'])
async def edit_note(request: Request, note_id: int, db_session=Depends(get_session)):
    form = await create_form(request, NoteForm)
    note = db_session.get(Note, note_id)
    if form.validate_on_submit():
        note.title = form.title.data
        note.body = form.body.data
        db_session.commit()
        flash(request, 'Note updated.')
        return RedirectResponse(url_for(request, 'index'), status_code=302)
    if request.method == 'GET':
        # pre-fill form
        form.title.data = note.title
        form.body.data = note.body
    return render_template(request, 'edit_note.html', form=form)


@app.post('/delete/{note_id:int}')
async def delete_note(request: Request, note_id: int, db_session=Depends(get_session)):
    form = await create_form(request, DeleteNoteForm)
    if form.validate_on_submit():
        note = db_session.get(Note, note_id)
        db_session.delete(note)
        db_session.commit()
        flash(request, 'Note deleted.')
    else:
        flash(request, 'Delete failed, please try again.')
    return RedirectResponse(url_for(request, 'index'), status_code=302)


if __name__ == '__main__':
    cli()
