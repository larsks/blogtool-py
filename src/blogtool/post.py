import datetime
import logging
import re
import string
import yaml

from dataclasses import dataclass, field, asdict
from pathlib import Path

from blogtool.itertools import takeuntil

LOG = logging.getLogger(__name__)
RE_FILENAME = re.compile(r'(?P<date>\d{4}-\d\d-\d\d)-(?P<slug>[^.]+)\.md')
MAX_SLUG_LENGTH = 30


def stripped(fd):
    for line in fd:
        yield line.rstrip()


@dataclass
class Post:
    '''A blog post.

    Creating a new post:

    >>> post = Post(title='This is a test')

    Creating from an existing post:

    >>> post = Post.from_file('2021-02-01-example-post.md')
    '''

    title: str

    slug: str = field(default=None)
    date: datetime.datetime = field(default=None)
    tags: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    weight: int = field(default=None)
    draft: bool = field(default=None)
    properties: dict = field(default_factory=dict)
    slug: str = field(default=None)
    content: str = field(default='', repr=False)

    exclude_from_export = [
        'date',
        'content',
    ]

    exclude_from_import = [
        'filename',
    ]

    max_slug_length = MAX_SLUG_LENGTH

    def __post_init__(self):
        if self.slug is None:
            self.slug = Post.slug_from_title(self.title)

        if self.date is None:
            self.date = datetime.datetime.now()

        if isinstance(self.date, str):
            self.date = self.parse_date(self.date)

    @property
    def filename(self):
        return f'{self.date_as_string}-{self.slug}.md'

    @classmethod
    def from_file(cls, path):
        path = Path(path)

        with path.open('r') as fd:
            metadata = cls.read_metadata(fd)
            if not metadata:
                LOG.warning('no metadata in %s', path)

            content = fd.read()

        metadata = {
            k: v
            for k, v in metadata.items()
            if k not in cls.exclude_from_import
        }

        return cls(content=content, **metadata)

    @staticmethod
    def parse_date(s):
        return datetime.datetime.strptime(s, '%Y-%m-%d')

    @classmethod
    def slug_from_title(cls, title):
        slug = ''.join(c for c in title
                       if c in string.ascii_letters + string.digits + '-_ '
                       ).replace(' ', '-').lower()[:cls.max_slug_length]
        return slug.rstrip('-')

    @classmethod
    def read_metadata(cld, fd):
        lines = []

        data = stripped(fd)

        if next(data, None) != '---':
            return {}

        lines = takeuntil(lambda line: line == '---', data, include_match=False)

        return yaml.safe_load('\n'.join(lines))

    @property
    def date_as_string(self):
        return self.date.strftime('%Y-%m-%d')

    @property
    def metadata(self):
        data = {
            k: v
            for k, v in asdict(self).items()
            if k not in self.exclude_from_export
            and v not in [None, [], {}, ()]
        }

        data['date'] = self.date_as_string
        data['filename'] = self.filename

        return data

    def to_string(self):
        return '\n'.join([
            '---',
            yaml.safe_dump(self.metadata, default_flow_style=False),
            '---',
            self.content
        ])
