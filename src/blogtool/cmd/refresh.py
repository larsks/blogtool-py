import click
import contextlib
import datetime
import logging

from itertools import zip_longest
from pathlib import Path

from blogtool.itertools import takeuntil
from blogtool.post import Post

LOG = logging.getLogger(__name__)


@contextlib.contextmanager
def checkout(repo, branch):
    old_branch = repo.head.ref

    if old_branch != branch:
        if repo.index.diff(None):
            raise click.ClickException(
                f'attempt to switch {old_branch.name} -> {branch.name} with unstaged changes')
        branch.checkout()

    try:
        yield
    finally:
        if old_branch != branch:
            if repo.index.diff(None):
                raise click.ClickException(
                    f'attempt to switch {branch.name} -> {old_branch.name} with unstaged changes')

            old_branch.checkout()


def find_posts(ctx, branch, merge_base):
    '''find all post/* files between merge_base and branch'''

    cur = branch.commit
    posts = set()

    # get a list of commits from merge_base to branch.
    commits = list(
        reversed(
            list(
                takeuntil(
                    lambda commit: commit == merge_base,
                    ctx.repo.iter_commits(branch)
                )
            )
        )
    )

    # iterate over (previous, current) commits, looking for
    # added, renamed, or deleted files.
    for prev, cur in zip_longest(commits, commits[1:]):
        if cur is None:
            break

        LOG.debug('examining commit %s', cur)
        diff_index = prev.diff(cur)
        for diff in diff_index:
            LOG.debug('change_type %s a_path %s b_path %s',
                      diff.change_type, diff.a_path, diff.b_path)
            if diff.change_type in ['A', 'R']:
                if diff.a_path.startswith('post/'):
                    LOG.info('found post %s', diff.b_path)
                    posts.add(Path(diff.b_path))

            if diff.change_type in ['R', 'D']:
                LOG.debug('discarding %s', diff.a_path)
                posts.discard(Path(diff.a_path))

        cur = cur.parents[0]

    return posts


@click.command()
@click.option('--date', '-d', type=Post.parse_date)
@click.argument('draft_name', default='HEAD')
@click.pass_obj
def refresh(ctx, date, draft_name):
    if draft_name == 'HEAD':
        draft_name = ctx.repo.head.ref.name

    for i in [draft_name, f'draft/{draft_name}']:
        try:
            branch = ctx.repo.refs[draft_name]
            break
        except IndexError:
            pass
    else:
        raise click.ClickException(f'no draft named {draft_name}')

    if ctx.repo.index.diff(None):
        raise click.ClickException('cannot operate when there are unstaged changes')

    LOG.info('processing branch %s', branch.name)
    with checkout(ctx.repo, branch):
        try:
            merge_base = ctx.repo.merge_base(ctx.main_branch, branch)[0]
        except IndexError:
            raise click.ClickException(f'failed to find merge base for {draft_name}')

        LOG.info('found merge base %s', merge_base)

        posts = find_posts(ctx, branch, merge_base)

        if len(posts) < 1:
            raise click.ClickException(f'no posts in {draft_name}')

        if date is None:
            date = datetime.datetime.now()

        LOG.info('setting date to %s', date.strftime('%Y-%m-%d'))

        for path in posts:
            post = Post.from_file(path)
            post.date = date
            new_path = path.parent / post.filename

            if new_path != path:
                LOG.info('renaming %s -> %s', path, new_path)
                with new_path.open('w') as fd:
                    fd.write(post.to_string())

                path.unlink()

                ctx.repo.git.add(path)
                ctx.repo.git.add(new_path)

        if ctx.repo.index.diff('HEAD'):
            LOG.info('committing changes')
            ctx.repo.git.commit(message=f'updated to date {date.strftime("%Y-%m-%d")}')
        else:
            LOG.info('no changes')
