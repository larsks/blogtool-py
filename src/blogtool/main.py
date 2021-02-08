import click
import git
import logging

from pathlib import Path

from dataclasses import dataclass

import blogtool

from blogtool.cmd import newpost
from blogtool.cmd import refresh
from blogtool.cmd import lsdraft

LOG = logging.getLogger(__name__)


@dataclass
class Context:
    repo: git.Repo = None
    main_branch: git.Head = None
    post_directory: Path = None


@click.group(context_settings={'auto_envvar_prefix': 'BLOGTOOL_'})
@click.option('--verbose', '-v', count=True)
@click.option('--main-branch', '-M', 'main_branch_name', default='master')
@click.option('--post-directory', '-P', default='post/', type=Path)
@click.pass_context
def main(ctx, verbose, main_branch_name, post_directory):
    try:
        repo = git.Repo(search_parent_directories=True)
    except git.exc.InvalidGitRepositoryError:
        raise click.ClickException(
            'blogtool must be run from inside a git repository')

    try:
        main_branch = repo.refs[main_branch_name]
    except IndexError:
        raise click.ClickException(
            f'no branch named {main_branch_name} in this repository')

    ctx.obj = Context(
        repo=repo,
        main_branch=main_branch,
        post_directory=post_directory,
    )

    try:
        loglevel = ['WARNING', 'INFO', 'DEBUG'][verbose]
    except IndexError:
        loglevel = 'DEBUG'

    logging.basicConfig(level=loglevel)


@main.command()
def version():
    print(f'blogtool {blogtool.__version__}')


main.add_command(newpost.newpost)
main.add_command(refresh.refresh)
main.add_command(lsdraft.lsdraft)
