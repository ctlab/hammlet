import click
from tabulate import tabulate

from ..models import models_H1, models_H2, models_mapping_mnemonic, models_hierarchy
from ..optimizer import Optimizer
from ..parsers import presets_db, parse_best, parse_input, parse_models
from ..printers import (log, log_br, log_debug, log_info, log_success, log_warn, print_a, print_input,
                        print_model_results, print_permutation, print_model_result_boot)
from ..utils import autotimeit, pformatf, get_a, get_chains, morph4
from ..version import version as __version__


@click.command()
@click.option('-m', '--model', 'models', multiple=True, metavar='<name...|all>',
              required=True, callback=parse_models,
              help='Comma-separated list of models (e.g. 2H1)')
@click.option('--theta', nargs=5, type=float, metavar='<n0 T1 T3 g1 g3>', required=True,
              help='Space-separated list of ' + click.style('five', bold=True) + ' theta components')
@click.option('-r', nargs=4, metavar='<float...>', type=float,
              default=(1, 1, 1, 1), show_default=True,
              help='Space-separated list of ' + click.style('four', bold=True) + ' r values')
@autotimeit
def calculate_aij(models, theta, r):
    """Calculate a_ij."""

    log_info('theta = ({})'.format(', '.join(pformatf(x, 3) for x in theta)))
    log_info('r = ({})'.format(', '.join(pformatf(x, 3) for x in r)))

    # log_info('Calculating a_ij values...')
    for model in models:
        theta_ = model.apply_bounds(theta)
        a = get_a(model, theta_, r)
        log_success('a_ij for model {} ({}): {}'
                    .format(model.name, model.mnemonic_name,
                            ', '.join(pformatf(a_ij, 3) for a_ij in a)))
