import click


@click.command()
@click.pass_obj
def lsdraft(ctx):
    drafts = [branch for branch in ctx.repo.branches
              if branch.name.startswith('draft/')]

    print('\n'.join(draft.name for draft in drafts))
