from collections import OrderedDict

import click

from .commands import mle, calculate_aij, show_permutation, draw, chains, levels
from .version import version as __version__


CONTEXT_SETTINGS = dict(
    max_content_width=999,
    help_option_names=['-h', '--help'],
)


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
    pass


# Note: respect the desired order
cli.add_command(mle)
cli.add_command(calculate_aij)
cli.add_command(show_permutation)
cli.add_command(draw)
cli.add_command(chains)
cli.add_command(levels)

if __name__ == '__main__':
    cli()
