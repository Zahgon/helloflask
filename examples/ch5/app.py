import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from fastapi import FastAPI
from sqlalchemy import String, Text, MetaData, ForeignKey, Column, Table, create_engine, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.pool import StaticPool

SQLITE_PREFIX = 'sqlite:///' if sys.platform.startswith('win') else 'sqlite:////'
SQLITE_PATH = Path(__file__).resolve().parent / 'data.db'


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
    'SECRET_KEY': os.getenv('SECRET_KEY', 'secret string'),
    'SQLALCHEMY_DATABASE_URI': os.getenv('DATABASE_URL', SQLITE_PREFIX + str(SQLITE_PATH)),
}
engine = create_db_engine(config['SQLALCHEMY_DATABASE_URI'])


# models
class Note(Base):
    __tablename__ = 'note'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(50))
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    updated_at: Mapped[Optional[datetime]] = mapped_column(onupdate=datetime.now)

    def __repr__(self):
        return f'<Note {self.id}: {self.title}>'


# one to many / many to one
class Author(Base):
    __tablename__ = 'author'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(20))
    phone: Mapped[Optional[str]] = mapped_column(String(11))

    articles: Mapped[list['Article']] = relationship(back_populates='author')

    def __repr__(self):
        return f'<Author {self.id}: {self.name}>'


class Article(Base):
    __tablename__ = 'article'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(50))
    body: Mapped[str] = mapped_column(Text)
    author_id: Mapped[int] = mapped_column(ForeignKey('author.id'))

    author: Mapped['Author']  = relationship(back_populates='articles')

    def __repr__(self):
        return f'<Article {self.id}: {self.title}>'


# one to one
class Country(Base):
    __tablename__ = 'country'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)

    capital: Mapped['Capital'] = relationship(back_populates='country')

    def __repr__(self):
        return f'<Country {self.id}: {self.name}>'


class Capital(Base):
    __tablename__ = 'capital'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(30), unique=True)
    country_id: Mapped[int] = mapped_column(ForeignKey('country.id'))

    country: Mapped['Country']  = relationship(back_populates='capital')

    def __repr__(self):
        return f'<Capital {self.id}: {self.name}>'


# many to many
student_teacher = Table(
    'student_teacher',
    Base.metadata,
    Column('student_id', ForeignKey('student.id'), primary_key=True),
    Column('teacher_id', ForeignKey('teacher.id'), primary_key=True)
)


class Student(Base):
    __tablename__ = 'student'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(70), unique=True)
    grade: Mapped[str] = mapped_column(String(20))

    teachers: Mapped[list['Teacher']] = relationship(
        secondary=student_teacher,
        back_populates='students'
    )

    def __repr__(self):
        return f'<Student {self.id}: {self.name}>'


class Teacher(Base):
    __tablename__ = 'teacher'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(70), unique=True)
    office: Mapped[str] = mapped_column(String(20))

    students: Mapped[list['Student']] = relationship(
        secondary=student_teacher,
        back_populates='teachers'
    )

    def __repr__(self):
        return f'<Teacher {self.id}: {self.name}>'


# many to many with extra data
class Collection(Base):
    __tablename__ = 'collection'

    user_id: Mapped[int] = mapped_column(ForeignKey('user.id'), primary_key=True)
    photo_id: Mapped[int] = mapped_column(ForeignKey('photo.id'), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)
    note: Mapped[Optional[str]] = mapped_column(Text)

    user: Mapped['User'] = relationship(back_populates='collections', lazy='joined')
    photo: Mapped['Photo'] = relationship(back_populates='collections', lazy='joined')

    def __repr__(self):
        return f'<Collection {self.user_id}-{self.photo_id}: {self.user.name}-{self.photo.filename}>'


class User(Base):
    __tablename__ = 'user'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)

    collections: Mapped[list['Collection']] = relationship(
        back_populates='user',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<User {self.id}: {self.name}>'


class Photo(Base):
    __tablename__ = 'photo'

    id: Mapped[int] = mapped_column(primary_key=True)
    filename: Mapped[str] = mapped_column(String(255), unique=True)

    collections: Mapped[list['Collection']] = relationship(
        back_populates='photo',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<Photo {self.id}: {self.filename}>'


# cascade and event listener
class Post(Base):
    __tablename__ = 'post'

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String(50))
    body: Mapped[Optional[str]] = mapped_column(Text)
    edited_count: Mapped[int] = mapped_column(default=0)

    comments: Mapped[list['Comment']] = relationship(
        back_populates='post',
        cascade='all, delete-orphan'
    )


class Comment(Base):
    __tablename__ = 'comment'

    id: Mapped[int] = mapped_column(primary_key=True)
    body: Mapped[Optional[str]] = mapped_column(Text)
    post_id: Mapped[int] = mapped_column(ForeignKey('post.id'))

    post: Mapped['Post'] = relationship(back_populates='comments')


@event.listens_for(Post.body, 'set')
def increment_edited_count(target, value, oldvalue, initiator):
    if target.edited_count is not None:
        target.edited_count += 1


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


if __name__ == '__main__':
    cli()
