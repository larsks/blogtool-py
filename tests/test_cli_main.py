import git
import os
import pytest
import tempfile

from click.testing import CliRunner
from pathlib import Path

import blogtool
import blogtool.main


@pytest.fixture
def repo():
    with tempfile.TemporaryDirectory(dir='.', prefix='repo') as tmpdir:
        repo = git.Repo.init(tmpdir)

        # git will complain if these aren't set
        with repo.config_writer() as cw:
            cw.set_value('user', 'name', 'Py Test')
            cw.set_value('user', 'email', 'pytest@example.com')

        saved_cwd = os.getcwd()
        os.chdir(tmpdir)
        yield repo
        os.chdir(saved_cwd)


@pytest.fixture
def repodir(repo):
    return Path(repo.working_tree_dir)


@pytest.fixture
def repo_with_master(repo, repodir):
    postdir = (repodir / 'post')
    postdir.mkdir()
    with (postdir / '.gitkeep').open('w') as fd:
        fd.close()
    repo.index.add(str(postdir / '.gitkeep'))
    repo.index.commit('create post directory')

    return repo


@pytest.fixture
def runner():
    return CliRunner(mix_stderr=False)


def test_main_no_args(runner):
    res = runner.invoke(blogtool.main.main, [])
    assert res.exit_code == 0
    assert res.stdout.startswith('Usage:')


def test_main_version_with_empty_repository(repo, runner):
    res = runner.invoke(blogtool.main.main, ['version'])
    assert res.exit_code == 1


def test_main_version_with_non_empty_repository(repo_with_master, repodir, runner):
    res = runner.invoke(blogtool.main.main, ['version'])

    assert res.exit_code == 0
    assert res.stdout == f'blogtool {blogtool.__version__}\n'


def test_main_newpost_with_no_title(repo_with_master, repodir, runner):
    res = runner.invoke(blogtool.main.main, ['newpost'])
    assert res.exit_code == 2


def test_main_newpost_without_git(repo_with_master, repodir, runner):
    res = runner.invoke(blogtool.main.main,
                        ['newpost', '-d', '2021-01-01', 'Test post'])

    expected_path = repodir / 'post' / '2021-01-01-test-post.md'
    assert res.exit_code == 0
    assert expected_path.is_file()
    with expected_path.open('r') as fd:
        assert 'Test post' in fd.read()


def test_main_newpost_without_git_duplicate_file(repo_with_master, repodir, runner):
    runner.invoke(blogtool.main.main,
                  ['newpost', '-d', '2021-01-01', 'Test post'])
    res = runner.invoke(blogtool.main.main,
                        ['newpost', '-d', '2021-01-01', 'Test post'])
    assert res.exit_code == 1
    assert res.stderr == 'Error: a post named post/2021-01-01-test-post.md already exists\n'


def test_main_newpost_with_git(repo_with_master, repodir, runner):
    res = runner.invoke(blogtool.main.main,
                        ['newpost', '-g', '-d', '2021-01-01', 'Test post'])

    expected_path = repodir / 'post' / '2021-01-01-test-post.md'

    assert res.exit_code == 0
    assert expected_path.is_file()
    assert 'draft/test-post' in repo_with_master.refs
    assert repo_with_master.head.ref.name == 'draft/test-post'
    assert repo_with_master.head.commit.tree.trees[0].blobs[1].name == expected_path.name


def test_main_newpost_with_git_duplicate_file(repo_with_master, repodir, runner):
    runner.invoke(blogtool.main.main,
                  ['newpost', '-g', '-d', '2021-01-01', 'Test post'])

    # swithc back to master branch
    repo_with_master.refs['master'].checkout()

    res = runner.invoke(blogtool.main.main,
                        ['newpost', '-g', '-d', '2021-01-01', 'Test post'])
    assert res.exit_code == 1
    assert isinstance(res.exception, SystemExit)
    assert res.stderr == 'Error: a branch named draft/test-post already exists\n'


def test_main_refresh_with_explicit_date(repo_with_master, repodir, runner):
    res = runner.invoke(blogtool.main.main,
                        ['newpost', '-g', '-d', '2021-01-01', 'Test post'])
    assert res.exit_code == 0

    branch = repo_with_master.head.ref

    res = runner.invoke(blogtool.main.main, ['refresh', '-d', '2021-02-02'])
    assert res.exit_code == 0

    expected_path = repodir / 'post' / '2021-02-02-test-post.md'
    assert expected_path.is_file()

    assert len(list(repo_with_master.iter_commits(branch))) == 3


def test_main_refresh_with_unstaged_changes(repo_with_master, repodir, runner):
    res = runner.invoke(blogtool.main.main,
                        ['newpost', '-g', '-d', '2021-01-01', 'Test post'])
    expected_path = repodir / 'post' / '2021-01-01-test-post.md'

    assert res.exit_code == 0
    assert expected_path.is_file()

    expected_path.unlink()
    res = runner.invoke(blogtool.main.main, ['refresh', '-d', '2021-02-02'])
    assert res.exit_code == 1
    assert res.stderr == 'Error: cannot operate when there are unstaged changes\n'


def test_main_lsdraft_with_no_drafts(repo_with_master, runner):
    res = runner.invoke(blogtool.main.main, ['lsdraft'])
    assert res.exit_code == 0
    assert res.stdout == '\n'


def test_main_lsdraft_with_drafts(repo_with_master, runner):
    runner.invoke(blogtool.main.main,
                  ['newpost', '-g', '-d', '2021-01-01', 'Test post 1'])
    runner.invoke(blogtool.main.main,
                  ['newpost', '-g', '-d', '2021-02-02', 'Test post 2'])
    res = runner.invoke(blogtool.main.main, ['lsdraft'])
    assert res.exit_code == 0
    assert res.stdout == 'draft/test-post-1\ndraft/test-post-2\n'
