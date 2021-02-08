import io
import logging
import tempfile
import yaml

from pathlib import Path

LOG = logging.getLogger(__name__)


def stripped(fd):
    for line in fd:
        yield line.rstrip()


class Post:
    '''A blog post'''

    def __init__(self, path):
        self.path = Path(path)
        self.filename = self.path.name
        self.date = self.filename[:10]
        self.stub = self.filename[11:-3]

        with self.path.open() as fd:
            self.metadata = self.read_metadata(fd)

    def __repr__(self):
        return f'<Post {self.stub} @ {self.date}>'

    def change_date(self, date):
        date_str = date.strftime('%Y-%m-%d')
        self.filename = f'{date_str}-{self.stub}.md'
        self.metadata['date'] = date_str
        self.metadata['filename'] = self.filename
        self.write_metadata()
        old_path = self.path
        self.path = self.path.rename(self.path.parent / self.filename)

        return (old_path, self.path)

    def read_metadata(self, fd):
        md = io.StringIO()

        for ln, line in enumerate(stripped(fd)):
            if ln == 0:
                if line != '---':
                    LOG.warning('no metadata in %s', self.path)
                    return {}
            else:
                if line == '---':
                    break
                else:
                    md.write(line)
                    md.write('\n')

        return yaml.safe_load(md.getvalue())

    def write_metadata(self):
        with self.path.open() as fd, tempfile.NamedTemporaryFile(
                mode='w', dir=self.path.parent, prefix='post') as tmp:
            self.read_metadata(fd)
            tmp.write('---\n')
            tmp.write(yaml.safe_dump(self.metadata, default_flow_style=False))
            tmp.write('---\n')
            tmp.write(fd.read())

            self.path.unlink()
            Path(tmp.name).link_to(self.path)



