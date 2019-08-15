import csv
import sys

import click
from tabulate import tabulate

from ..optimizer import Optimizer
from ..parsers import presets_db, parse_input
from ..printers import log_debug, log_info, log_success, log_warn
from ..models import models_mapping_mnemonic
from ..utils import autotimeit, pformatf, get_chain


@click.command()
@click.option('-l', '--levels', 'levels_filename', metavar='<path|->',
              type=click.Path(exists=True, allow_dash=True),
              help='File with levels data')
@click.option('--preset', type=click.Choice(presets_db), metavar='<preset>',
              help='Data preset ({})'.format('/'.join(presets_db.keys())))
@click.option('-y', nargs=10, type=int, metavar='<int...>',
              help='Space-separated list of ' + click.style('ten', bold=True) +
              ' y values (y11 y12 y13 y14 y22 y23 y24 y33 y34 y44)')
@click.option('-r', nargs=4, type=float, metavar='<float...>',
              default=(1, 1, 1, 1), show_default=True,
              help='Space-separated list of ' + click.style('four', bold=True) + ' r values')
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
def levels(levels_filename, preset, y, r,
           critical_pvalue, method, theta0, debug):
    """Compute levels."""

    y = parse_input(preset, y, verbose=True)
    del preset
    log_info('y: {}'.format(' '.join(map(str, y))))
    log_info('r: ({})'.format(', '.join(map(pformatf, r))))

    if not theta0:
        theta0 = (round(0.6 * sum(y), 5), 0.5, 0.5, 0.5, 0.5)
        if debug:
            log_debug('Using default theta0: {}'.format(theta0))

    def parse_perm(perm):
        if perm.startswith('{') or perm.startswith('('):
            perm = perm[1:]
        if perm.endswith('}') or perm.endswith(')'):
            perm = perm[:-1]
        return tuple(map(int, perm.split(',')))

    log_info('Processing levels...'.format())
    levels_data = {level: [] for level in range(5)}  # {level: [(model, perm)]}
    if sys.version > '3':
        levels_file = open(levels_filename, newline='')
    else:
        levels_file = open(levels_filename, 'rb')
    with levels_file as f:
        reader = csv.DictReader(f)
        for row in reader:
            level = int(row['Level'])
            assert 0 <= level <= 4
            model = models_mapping_mnemonic['{}:{}'.format(row['Branch'], row['Case'])]
            if model.name != row['Type']:
                log_warn('Model name mismatch: model.name={}, Type={}'.format(model.name, row['Type']))
            perm = parse_perm(row['Permut'])
            levels_data[level].append((model, perm))
    del reader, row, level, model, perm, levels_file

    # ================
    from ..models import all_models
    missed_models = set(all_models) - set(model for (model, perm) in sum(levels_data.values(), []))
    if missed_models:
        log_warn('Missed models: {}'.format(' '.join(map(str, missed_models))))
    del all_models, missed_models
    # ================

    optimizer = Optimizer(y, r, theta0, method, debug=debug)
    results_level = {level: [] for level in levels_data}

    log_info('Optimizing...')
    for level, level_data in levels_data.items():
        for model, perm in level_data:
            result = optimizer.one(model, perm)
            results_level[level].append(result)
        results_level[level].sort(key=lambda t: t.LL, reverse=True)

    data = []
    for level in reversed(range(5)):
        for result in results_level[level]:
            model = result.model
            perm = result.permutation
            LL = result.LL
            n0, T1, T3, gamma1, gamma3 = result.theta
            data.append((level, model.name, model.mnemonic_name,
                         ','.join(map(str, perm)),
                         LL, n0, T1, T3, gamma1, gamma3))
            # ========
            if abs(LL - results_level[level][0].LL) < 1e-3:
                data[-1] = tuple(click.style(str(x), fg='yellow') for x in data[-1])
            # ========
            del result, model, perm, LL, n0, T1, T3, gamma1, gamma3
        del level
    table = tabulate(data,
                     headers=[click.style(s, bold=True) for s in ['Lvl', 'Model', 'Mnemo', 'Perm', 'LL', 'n0', 'T1', 'T3', 'g1', 'g3']],
                     numalign='center', stralign='center',
                     floatfmt='.3f', tablefmt='simple')
    log_success('MLE results:')
    click.echo(table)
    del data, table

    # was: max(results, key=lambda t: t.LL)
    # results are already sorted, so we can just pull the first one
    best_results_level = {level: results[0]
                          for level, results in results_level.items()}

    data = []
    for level in reversed(range(5)):
        result = best_results_level[level]
        model = result.model
        perm = result.permutation
        LL = result.LL
        n0, T1, T3, gamma1, gamma3 = result.theta
        data.append([level, model.name, model.mnemonic_name,
                     ','.join(map(str, perm)),
                     LL, n0, T1, T3, gamma1, gamma3])
        del result, model, perm, LL, n0, T1, T3, gamma1, gamma3
    table = tabulate(data,
                     headers=[click.style(s, bold=True) for s in ['Lvl', 'Model', 'Mnemo', 'Perm', 'LL', 'n0', 'T1', 'T3', 'g1', 'g3']],
                     numalign='center', stralign='center', floatfmt='.3f', tablefmt='simple')
    log_success('Best result on each level:')
    click.echo(table)
    del data, table

    log_info('Calculating chain...')
    path = [best_results_level[level].model.name for level in reversed(range(5))]
    results = {result.model.name: result for result in best_results_level.values()}
    chain = get_chain(path, results, critical_pvalue)
    log_success('Chain over levels:')
    click.echo('    ' + ' -> '.join('{}[{:.2f}]'.format(results[model].model.name, results[model].LL) for model in chain))

    simple_model = chain[-1]
    log_success('Insignificantly worse simple model: {}'.format(simple_model))
