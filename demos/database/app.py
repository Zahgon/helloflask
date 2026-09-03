# -*- coding: utf-8 -*-
"""
    :author: Grey Li (李辉)
    :url: http://greyli.com
    :copyright: © 2018 Grey Li
    :license: MIT, see LICENSE for more details.
"""
import code
import os
import sys
from pathlib import Path

import click
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text, create_engine, event, select
from sqlalchemy.orm import DeclarativeBase, relationship, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.middleware.sessions import SessionMiddleware
from wtforms import SubmitField, TextAreaField
from wtforms.validators import DataRequired

from helpers import BaseForm, create_form, flash, render_template, templates, url_for

# SQLite URI compatible
WIN = sys.platform.startswith('win')
if WIN:
    prefix = 'sqlite:///'
else:
    prefix = 'sqlite:////'

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI()
app.state.config = config = {
    'SECRET_KEY': os.getenv('SECRET_KEY', 'secret string'),
    'SQLALCHEMY_DATABASE_URI': os.getenv('DATABASE_URL', prefix + str(BASE_DIR / 'data.db')),
}
app.add_middleware(SessionMiddleware, secret_key=config['SECRET_KEY'])
app.mount('/static', StaticFiles(directory=BASE_DIR / 'static', check_dir=False), name='static')
templates.env.trim_blocks = True
templates.env.lstrip_blocks = True


class Base(DeclarativeBase):
    pass


def create_db_engine(url):
    """Create the database engine with SQLite friendly defaults."""
    options = {}
    if url.startswith('sqlite'):
        options['connect_args'] = {'check_same_thread': False}
        if ':memory:' in url or url.endswith('sqlite://'):
            options['poolclass'] = StaticPool
    return create_engine(url, **options)


engine = create_db_engine(config['SQLALCHEMY_DATABASE_URI'])
Session = sessionmaker(bind=engine)


def get_session():
    """Provide a database session for the duration of the request."""
    with Session() as session:
        yield session


# handlers
def make_shell_context():
    return dict(engine=engine, Session=Session, Note=Note, Author=Author, Article=Article,
                Writer=Writer, Book=Book, Singer=Singer, Song=Song, Citizen=Citizen, City=City,
                Capital=Capital, Country=Country, Teacher=Teacher, Student=Student, Post=Post,
                Comment=Comment, Draft=Draft)


@click.group()
def cli():
    """Manage the application."""


@cli.command()
def shell():
    """Run an interactive shell with the application objects."""
    code.interact(local=dict(app=app, **make_shell_context()))


@cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')
def initdb(drop):
    """Initialize the database."""
    if drop:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    click.echo('Initialized database.')


# Forms
class NewNoteForm(BaseForm):
    body = TextAreaField('Body', validators=[DataRequired()])
    submit = SubmitField('Save')


class EditNoteForm(BaseForm):
    body = TextAreaField('Body', validators=[DataRequired()])
    submit = SubmitField('Update')


class DeleteNoteForm(BaseForm):
    submit = SubmitField('Delete')


# Models
class Note(Base):
    __tablename__ = 'note'

    id = Column(Integer, primary_key=True)
    body = Column(Text)

    # optional
    def __repr__(self):
        return '<Note %r>' % self.body


@app.get('/')
async def index(request: Request, db_session=Depends(get_session)):
    form = await create_form(request, DeleteNoteForm)
    notes = db_session.scalars(select(Note)).all()
    return render_template(request, 'index.html', notes=notes, form=form)


@app.api_route('/new', methods=['GET', 'POST'])
async def new_note(request: Request, db_session=Depends(get_session)):
    form = await create_form(request, NewNoteForm)
    if form.validate_on_submit():
        body = form.body.data
        note = Note(body=body)
        db_session.add(note)
        db_session.commit()
        flash(request, 'Your note is saved.')
        return RedirectResponse(url_for(request, 'index'), status_code=302)
    return render_template(request, 'new_note.html', form=form)


@app.api_route('/edit/{note_id:int}', methods=['GET', 'POST'])
async def edit_note(request: Request, note_id: int, db_session=Depends(get_session)):
    form = await create_form(request, EditNoteForm)
    note = db_session.get(Note, note_id)
    if form.validate_on_submit():
        note.body = form.body.data
        db_session.commit()
        flash(request, 'Your note is updated.')
        return RedirectResponse(url_for(request, 'index'), status_code=302)
    form.body.data = note.body  # preset form input's value
    return render_template(request, 'edit_note.html', form=form)


@app.post('/delete/{note_id:int}')
async def delete_note(request: Request, note_id: int, db_session=Depends(get_session)):
    form = await create_form(request, DeleteNoteForm)
    if form.validate_on_submit():
        note = db_session.get(Note, note_id)
        db_session.delete(note)
        db_session.commit()
        flash(request, 'Your note is deleted.')
    else:
        raise HTTPException(status_code=400)
    return RedirectResponse(url_for(request, 'index'), status_code=302)


# one to many
class Author(Base):
    __tablename__ = 'author'

    id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True)
    phone = Column(String(20))
    articles = relationship('Article')  # collection

    def __repr__(self):
        return '<Author %r>' % self.name


class Article(Base):
    __tablename__ = 'article'

    id = Column(Integer, primary_key=True)
    title = Column(String(50), index=True)
    body = Column(Text)
    author_id = Column(Integer, ForeignKey('author.id'))

    def __repr__(self):
        return '<Article %r>' % self.title


# many to one
class Citizen(Base):
    __tablename__ = 'citizen'

    id = Column(Integer, primary_key=True)
    name = Column(String(70), unique=True)
    city_id = Column(Integer, ForeignKey('city.id'))
    city = relationship('City')  # scalar

    def __repr__(self):
        return '<Citizen %r>' % self.name


class City(Base):
    __tablename__ = 'city'

    id = Column(Integer, primary_key=True)
    name = Column(String(30), unique=True)

    def __repr__(self):
        return '<City %r>' % self.name


# one to one
class Country(Base):
    __tablename__ = 'country'

    id = Column(Integer, primary_key=True)
    name = Column(String(30), unique=True)
    capital = relationship('Capital', back_populates='country', uselist=False)  # collection -> scalar

    def __repr__(self):
        return '<Country %r>' % self.name


class Capital(Base):
    __tablename__ = 'capital'

    id = Column(Integer, primary_key=True)
    name = Column(String(30), unique=True)
    country_id = Column(Integer, ForeignKey('country.id'))
    country = relationship('Country', back_populates='capital')  # scalar

    def __repr__(self):
        return '<Capital %r>' % self.name


# many to many with association table
association_table = Table('association',
                          Base.metadata,
                          Column('student_id', Integer, ForeignKey('student.id')),
                          Column('teacher_id', Integer, ForeignKey('teacher.id'))
                          )


class Student(Base):
    __tablename__ = 'student'

    id = Column(Integer, primary_key=True)
    name = Column(String(70), unique=True)
    grade = Column(String(20))
    teachers = relationship('Teacher',
                            secondary=association_table,
                            back_populates='students')  # collection

    def __repr__(self):
        return '<Student %r>' % self.name


class Teacher(Base):
    __tablename__ = 'teacher'

    id = Column(Integer, primary_key=True)
    name = Column(String(70), unique=True)
    office = Column(String(20))
    students = relationship('Student',
                            secondary=association_table,
                            back_populates='teachers')  # collection

    def __repr__(self):
        return '<Teacher %r>' % self.name


# one to many + bidirectional relationship
class Writer(Base):
    __tablename__ = 'writer'

    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True)
    books = relationship('Book', back_populates='writer')

    def __repr__(self):
        return '<Writer %r>' % self.name


class Book(Base):
    __tablename__ = 'book'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), index=True)
    writer_id = Column(Integer, ForeignKey('writer.id'))
    writer = relationship('Writer', back_populates='books')

    def __repr__(self):
        return '<Book %r>' % self.name


# one to many + bidirectional relationship + use backref to declare bidirectional relationship
class Singer(Base):
    __tablename__ = 'singer'

    id = Column(Integer, primary_key=True)
    name = Column(String(70), unique=True)
    songs = relationship('Song', backref='singer')

    def __repr__(self):
        return '<Singer %r>' % self.name


class Song(Base):
    __tablename__ = 'song'

    id = Column(Integer, primary_key=True)
    name = Column(String(50), index=True)
    singer_id = Column(Integer, ForeignKey('singer.id'))

    def __repr__(self):
        return '<Song %r>' % self.name


# cascade
class Post(Base):
    __tablename__ = 'post'

    id = Column(Integer, primary_key=True)
    title = Column(String(50))
    body = Column(Text)
    comments = relationship('Comment', back_populates='post', cascade='all, delete-orphan')  # collection


class Comment(Base):
    __tablename__ = 'comment'

    id = Column(Integer, primary_key=True)
    body = Column(Text)
    post_id = Column(Integer, ForeignKey('post.id'))
    post = relationship('Post', back_populates='comments')  # scalar


# event listening
class Draft(Base):
    __tablename__ = 'draft'

    id = Column(Integer, primary_key=True)
    body = Column(Text)
    edit_time = Column(Integer, default=0)


@event.listens_for(Draft.body, 'set')
def increment_edit_time(target, value, oldvalue, initiator):
    if target.edit_time is not None:
        target.edit_time += 1

# same with:
# @event.listens_for(Draft.body, 'set', named=True)
# def increment_edit_time(**kwargs):
#     if kwargs['target'].edit_time is not None:
#         kwargs['target'].edit_time += 1


if __name__ == '__main__':
    cli()
