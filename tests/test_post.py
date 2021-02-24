import datetime
import io
import pytest

from contextlib import contextmanager
from unittest import mock

import blogtool.post


class fake_path_object:
    def __init__(self, name, content):
        self.name = name
        self.content = content

    @contextmanager
    def open(self, *args):
        buf = io.StringIO()
        buf.write(self.content)
        buf.seek(0)

        self._buf = buf

        yield buf


def test_create_no_title():
    with pytest.raises(TypeError):
        blogtool.post.Post()


def test_create_title():
    now = datetime.datetime.now()
    title = 'This is a test'

    post = blogtool.post.Post(title=title)

    assert post.title == title
    assert all(getattr(now, x) == getattr(post.date, x)
               for x in ['year', 'month', 'day'])
    assert post.slug == 'this-is-a-test'
    assert post.filename == now.strftime('%Y-%m-%d-this-is-a-test.md')
    assert post.tags == []
    assert post.categories == []


def test_metadata():
    now = datetime.datetime.now()
    title = 'This is a test'
    tags = ['tag1', 'tag2']
    post = blogtool.post.Post(title=title, tags=tags)

    assert post.metadata['date'] == now.strftime('%Y-%m-%d')
    assert post.metadata['tags'] == tags
    assert 'categories' not in post.metadata


def test_from_file():
    doc = fake_path_object('test-file.md', '\n'.join([
        '---',
        'title: Test File',
        'date: 2021-02-1',
        'tags:',
        '  - tag1',
        '  - tag2',
        '---',
        '',
        'This is test content.'
    ]))

    with mock.patch('blogtool.post.Path') as fake_path:
        fake_path.return_value = doc
        post = blogtool.post.Post.from_file('testfile.md')

    assert post.title == 'Test File'
    assert post.content == '\nThis is test content.'
    assert post.date.year == 2021
    assert post.date.month == 2
    assert post.date.day == 1
    assert post.tags == ['tag1', 'tag2']


def test_from_file_empty():
    doc = fake_path_object('test-file.md', '')

    with mock.patch('blogtool.post.Path') as fake_path:
        fake_path.return_value = doc
        with pytest.raises(TypeError):
            blogtool.post.Post.from_file('testfile.md')
