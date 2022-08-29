from collections import OrderedDict

import click

from . import __version__, commands
from .models import all_models
from .printers import log_info

CONTEXT_SETTINGS = dict(max_content_width=999, help_option_names=["-h", "--help"])


class GroupWithUnsortedCommands(click.Group):
    def __init__(self, *args, **kwargs):
        super(GroupWithUnsortedCommands, self).__init__(*args, **kwargs)
        # Ensure self.commands are stored in the insertion order
        self.commands = OrderedDict(self.commands)

    def list_commands(self, ctx):
        # Originally, in click.Group: `sorted(self.commands)`
        return tuple(self.commands.keys())


@click.group(
    cls=GroupWithUnsortedCommands,
    context_settings=CONTEXT_SETTINGS,
    invoke_without_command=True,
)
@click.pass_context
@click.option(
    "-l",
    "--list",
    "is_list_models",
    is_flag=True,
    help="List all models",
)
@click.version_option(__version__)
def cli(ctx, is_list_models):
    """Hybridization Models Maximum Likelihood Estimator

    Author: Konstantin Chukharev (lipen00@gmail.com)
    """

    if ctx.invoked_subcommand is None:
        if is_list_models:
            log_info("List of all models:")
            for model in all_models:
                click.echo("  - {!r}".format(model))
    else:
        # Invoking subcommand {ctx.invoked_subcommand}
        pass


# Note: respect the desired order
# cli.add_command(commands.mle)
cli.add_command(commands.mle_nr)
cli.add_command(commands.bootstrap)
cli.add_command(commands.bootstrap_LL)
cli.add_command(commands.calculate_aij)
# cli.add_command(commands.show_permutation)
cli.add_command(commands.draw)
# cli.add_command(commands.chains)
# cli.add_command(commands.levels)
cli.add_command(commands.stat_levels)
cli.add_command(commands.stat_reverse)

if __name__ == "__main__":
    cli()
