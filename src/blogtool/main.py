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
    main_branch: str = None
    post_directory: str = None


@click.group()
@click.option('--verbose', '-v', count=True)
@click.option('--main-branch', '-M', default='master')
@click.option('--post-directory', '-P', default='post/', type=Path)
@click.pass_context
def main(ctx, verbose, main_branch, post_directory):
    repo = git.Repo(search_parent_directories=True)

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
