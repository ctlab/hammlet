import click

from ..parsers import parse_best, parse_input, parse_models, parse_permutation
from ..printers import (log_br, log_debug, log_info, log_success, log_warn, print_a, print_input,
                        print_model_results, print_permutation, print_model_result_boot)
from ..utils import autotimeit, morph10


@click.command()
@click.option('--preset', metavar='<preset>',
              help='Preset data (laur/12-200/12-200-70-50/5-10/29-8...)')
@click.option('-y', nargs=10, type=int, metavar='<int...>',
              help='Space-separated list of ' + click.style('ten', bold=True) +
              ' y values (y11 y12 y13 y14 y22 y23 y24 y33 y34 y44)')
@click.option('-p', '--permutation', nargs=4, type=int, metavar='<int...>',
              callback=parse_permutation,
              help='Space-separated list of permutation indices (1 to 4)')
@click.option('--debug', is_flag=True,
              help='Debug.')
@autotimeit
def show_permutation(preset, y, permutation, debug):
    """Show permutation."""

    _, ys = parse_input(preset, None, None, y, verbose=True)
    del preset, y

    log_info('ys: {}'.format(' '.join(map(str, ys))))
    log_info('Permutation: ({})'.format(','.join(map(str, permutation))))

    perm = tuple(p - 1 for p in permutation)
    ys_ = morph10(ys, perm)
    log_success('Permuted ys: {}'.format(' '.join(map(str, ys_))))
