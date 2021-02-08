import click
import sys

from blogtool.post import Post


@click.command()
@click.option('-t', '--tag', 'tags', multiple=True)
@click.option('-c', '--category', 'categories', multiple=True)
@click.option('-d', '--date')
@click.option('-s', '--stub')
@click.option('-D', '--draft', is_flag=True)
@click.option('-g', '--git', is_flag=True)
@click.option('-G', '--git-add-only', is_flag=True)
@click.option('-S', '--stdout', is_flag=True)
@click.option('-w', '--weight', type=int)
@click.argument('title')
@click.pass_obj
def newpost(ctx, tags, categories, date, stub, git, stdout,
            draft, weight, git_add_only, title):

    # FIXME: this needs to be configureable
    if not categories:
        categories = ['tech']

    post = Post(
        title=title,
        tags=tags,
        categories=categories,
        date=date,
        stub=stub,
        draft=draft,
        weight=weight,
    )

    path = ctx.post_directory / post.filename
    branch = f'draft/{post.stub}'

    with (sys.stdout if stdout else open(path, 'w')) as fd:
        fd.write(post.to_string())

    if not stdout:
        if git:
            ctx.repo.git.checkout('master', B=branch)

        if git or git_add_only:
            ctx.repo.git.add(path)

        if git:
            ctx.repo.index.commit(f'added {path}')

        print(path)
