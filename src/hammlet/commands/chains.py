import itertools
from collections import OrderedDict

import click
from tabulate import tabulate

from ..optimizer import Optimizer
from ..parsers import presets_db, parse_best, parse_input, parse_models, parse_permutation
from ..printers import (log_br, log_debug, log_info, log_success, log_warn, print_a, print_input,
                        print_model_results, print_permutation, print_model_result_boot)
from ..models import models_H1, models_H2, models_hierarchy
from ..utils import autotimeit, pformatf, get_pvalues, get_paths, get_simple_models


@click.command()
@click.argument('chain', type=click.Choice(['H1', 'H2']), required=True)
@click.option('--preset', type=click.Choice(presets_db), metavar='<preset>',
              help='Data preset ({})'.format('/'.join(presets_db.keys())))
@click.option('-y', nargs=10, type=int, metavar='<int...>',
              help='Space-separated list of ' + click.style('ten', bold=True) +
              ' y values (y11 y12 y13 y14 y22 y23 y24 y33 y34 y44)')
@click.option('-r', nargs=4, type=float, metavar='<float...>',
              default=(1, 1, 1, 1), show_default=True,
              help='Space-separated list of ' + click.style('four', bold=True) + ' r values')
@click.option('--only-first', 'is_only_first', is_flag=True,
              help='Use only first permutation (1,2,3,4) for calculations')
@click.option('--only-permutation', metavar='<int...>',
              callback=parse_permutation,
              help='Comma-separated permutation of (1,2,3,4) to use for calculations')
@click.option('--free-permutation', 'is_free_permutation', is_flag=True,
              help='Use best permutation for each simpler model')
@click.option('-p', '--pvalue', 'critical_pvalue', type=float, metavar='<float>',
              default=0.05, show_default=True,
              help='p-value for statistical tests')
@click.option('--method', type=click.Choice(['SLSQP', 'L-BFGS-B', 'TNC']),
              default='SLSQP', show_default=True,
              help='Optimization method')
@click.option('--theta0', nargs=5, type=float, metavar='<n0 T1 T3 g1 g3>',
              help='Space-separated list of ' + click.style('five', bold=True) +
              ' initial theta components (n0 T1 T3 gamma1 gamma3)')
@click.option('--debug', is_flag=True, hidden=True,
              help='Debug')
@autotimeit
def chains(chain, preset, y, r, is_only_first, only_permutation, is_free_permutation,
           critical_pvalue, method, theta0, debug):
    """Compute chains."""

    y = parse_input(preset, y, verbose=True)
    del preset
    log_info('Model group: {}'.format(chain))
    log_info('Hierarchy: {}'.format('free' if is_free_permutation else 'non-free'))
    log_info('y: {}'.format(' '.join(map(str, y))))
    log_info('r: ({})'.format(', '.join(map(pformatf, r))))

    if not theta0:
        theta0 = (round(0.6 * sum(y), 5), 0.5, 0.5, 0.5, 0.5)
        if debug:
            log_debug('Using default theta0: {}'.format(theta0))

    if chain == 'H1':
        models = models_H1
    elif chain == 'H2':
        models = models_H2
    else:
        raise ValueError("Unsupperted chain '{}'".format(chain))
    hierarchy = models_hierarchy[chain]['free' if is_free_permutation else 'non-free']

    if is_only_first:
        perms = [(1, 2, 3, 4)]
    elif only_permutation:
        perms = [only_permutation]
    else:
        perms = list(itertools.permutations((1, 2, 3, 4)))

    optimizer = Optimizer(y, r, theta0, method, debug=debug)

    log_info('Searching for simplest models...')
    results_chain = OrderedDict()
    if is_free_permutation:
        for model in models:
            results = optimizer.many_perms(model, perms, sort=False)
            best_result = results[0]
            results_chain[model.name] = best_result

        del model, results, best_result
    else:
        model_complex = models[0]
        results_complex = optimizer.many_perms(model_complex, perms, sort=False)
        best_complex_result = results_complex[0]
        results_chain[model_complex.name] = best_complex_result
        # log_info('Best permutation for the most complex model: {}'
        #          .format(','.join(map(str, best_complex_result.permutation))))

        results = optimizer.many_models(models[1:], best_complex_result.permutation, sort=False)
        for result in results:
            results_chain[result.model.name] = result

        del model_complex, results_complex, best_complex_result, result, results

    data = []
    for m, result in results_chain.items():
        model = result.model
        assert m == model.name
        perm = result.permutation
        LL = result.LL
        n0, T1, T3, g1, g3 = result.theta
        data.append((model.name, model.mnemonic_name, ','.join(map(str, perm)), LL, n0, T1, T3, g1, g3))
    table = tabulate(data,
                     headers=[click.style(s, bold=True) for s in ['Model', 'Mnemo', 'Perm', 'LL', 'n0', 'T1', 'T3', 'g1', 'g3']],
                     numalign='center', stralign='center',
                     floatfmt='.3f', tablefmt='simple')
    log_success('MLE results:')
    click.echo(table)

    pvalues = get_pvalues(results_chain, hierarchy)
    data = []
    for (model_complex, model_simple), (stat, p) in pvalues.items():
        data.append((model_complex, model_simple, stat, p,
                     click.style('Yes', fg='green') if p >= critical_pvalue else click.style('No', fg='red')))
    del model_complex, model_simple, stat, p
    table = tabulate(data,
                     headers=['Complex', 'Simple', 'stat', 'p', '>crit'],
                     floatfmt=[None, None, '.3f', '.3f', None],
                     numalign='decimal', stralign='center',
                     missingval='-', tablefmt='simple')
    log_success('P-values:')
    click.echo(table)
    del data, table

    paths = get_paths(models[0].name, hierarchy)
    simple_models = get_simple_models(paths, pvalues, critical_pvalue)
    log_success('Insignificantly worse simple models: {}'.format(' '.join(simple_models)))
