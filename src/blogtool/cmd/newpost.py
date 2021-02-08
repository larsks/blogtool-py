import click
import datetime
import pathlib
import string
import sys
import yaml


@click.command()
@click.option('-t', '--tag', multiple=True)
@click.option('-c', '--category', multiple=True)
@click.option('-M', '--max-length', default=30, type=int)
@click.option('-d', '--date')
@click.option('-s', '--stub')
@click.option('-D', '--draft', is_flag=True)
@click.option('-g', '--git', is_flag=True)
@click.option('-G', '--git-add-only', is_flag=True)
@click.option('-S', '--stdout', is_flag=True)
@click.option('-w', '--weight', type=int)
@click.option('-P', '--post-directory', default='post', type=pathlib.Path)
@click.argument('title')
@click.pass_obj
def newpost(ctx, tag, category, max_length, date, stub, git, stdout,
            draft, weight, post_directory, git_add_only, title):
    metadata = {'title': title}

    if tag:
        metadata['tags'] = tag

    if category:
        metadata['categories'] = category
    else:
        metadata['categories'] = ['tech']

    if weight is not None:
        metadata['weight'] = weight

    if draft:
        metadata['draft'] = True

    if date:
        metadata['date'] = date
    else:
        metadata['date'] = datetime.datetime.now().strftime('%Y-%m-%d')

    stub = ''.join(c for c in title
                   if c in string.ascii_letters + string.digits + '-_ '
                   ).replace(' ', '-').lower()[:max_length]
    stub = stub.rstrip('-')
    metadata['stub'] = stub

    filename = '{}-{}.md'.format(metadata['date'], stub)
    branch = 'draft/{}'.format(stub)
    metadata['filename'] = filename
    path = post_directory / filename

    with (sys.stdout if stdout else open(path, 'w')) as fd:
        fd.write('\n'.join(['---',
                            yaml.safe_dump(metadata, default_flow_style=False),
                            '---', '', '']))

    if not stdout:
        if git:
            ctx.repo.git.checkout('master', B=branch)

        if git or git_add_only:
            ctx.repo.git.add(path)

        if git:
            ctx.repo.index.commit(f'added {path}')

        print(path)
