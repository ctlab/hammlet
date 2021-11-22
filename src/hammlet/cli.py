from collections import OrderedDict

import click

from . import __version__, commands

CONTEXT_SETTINGS = dict(max_content_width=999, help_option_names=["-h", "--help"])


class GroupWithUnsortedCommands(click.Group):
    def __init__(self, *args, **kwargs):
        super(GroupWithUnsortedCommands, self).__init__(*args, **kwargs)
        # Ensure self.commands are stored in the insertion order
        self.commands = OrderedDict(self.commands)

    def list_commands(self, ctx):
        # Originally, in click.Group: `sorted(self.commands)`
        return tuple(self.commands.keys())


@click.group(context_settings=CONTEXT_SETTINGS, cls=GroupWithUnsortedCommands)
@click.version_option(__version__)
def cli():
    """Hybridization Models Maximum Likelihood Estimator

    Author: Konstantin Chukharev (lipen00@gmail.com)
    """


# Note: respect the desired order
cli.add_command(commands.mle)
cli.add_command(commands.bootstrap)
cli.add_command(commands.bootstrap_LL)
cli.add_command(commands.calculate_aij)
cli.add_command(commands.show_permutation)
cli.add_command(commands.draw)
cli.add_command(commands.chains)
cli.add_command(commands.levels)
# cli.add_command(commands.stat_chains)
cli.add_command(commands.stat_levels)
cli.add_command(commands.stat_reverse)

if __name__ == "__main__":
    cli()
