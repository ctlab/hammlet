from __future__ import division

import time
from multiprocessing import Pool
from itertools import permutations
from collections import OrderedDict

import click

from .parsers import *
from .printers import *
from .utils import *
from version import __version__


@click.command(context_settings=dict(
    max_content_width=999,
    help_option_names=['-h', '--help'],
))
@click.option('-i', '--input', 'filename', metavar='<path|->',
              type=click.Path(exists=True, allow_dash=True),
              help='File with markers presence/absence data')
@click.option('--laur', is_flag=True,
              help='Use laurasiatherian data')
@click.option('-n', '--names', nargs=4, metavar='<name...>',
              default=('Name1', 'Name2', 'Name3', 'Name4'),
              help='Space-separated list of ' + click.style('four', bold=True) + ' species names')
@click.option('-y', nargs=10, metavar='<int...>', type=int,
              help='Space-separated list of ' + click.style('ten', bold=True) +
                   ' y values (y11 y12 y13 y14 y22 y23 y24 y33 y34 y44)')
@click.option('-r', nargs=4, metavar='<float...>', type=float,
              default=(1, 1, 1, 1), show_default=True,
              help='Space-separated list of ' + click.style('four', bold=True) + ' r values')
@click.option('-m', '--model', 'model_names', multiple=True, metavar='<int|all>', callback=parse_models,
              help='Which model to use. Pass multiple times to use many models. '
                   'Pass "all" to use all available models (default behaviour)')
@click.option('--best', metavar='<int|all>', callback=parse_best,
              default='all', show_default=True,
              help='Number of best models to show')
@click.option('--method', type=click.Choice(['SLSQP', 'L-BFGS-B', 'TNC']),
              default='SLSQP', show_default=True,
              help='Optimization method')
@click.option('--theta0', nargs=5, type=float, metavar='<n0 T1 T3 g1 g3>',
              help='Space-separated list of ' + click.style('five', bold=True) +
                   ' initial theta components (n0 T1 T3 gamma1 gamma3)')
@click.option('--only-first', is_flag=True,
              help='Do calculations only for first (initial) permutation')
@click.option('--only-a', is_flag=True,
              help='Do only a_ij calculations')
@click.option('--no-polytomy', is_flag=True,
              help='Do not show polytomy results')
@click.option('--compact', is_flag=True,
              help='Compact results (for batch-mode')
@click.option('-p', '--parallel', type=int, metavar='<int>',
              default=1, show_default=True,
              help='Number of parallel optimizing processes')
@click.option('--test', is_flag=True,
              help='Run test')
@click.option('--debug', is_flag=True,
              help='Debug')
@click.version_option(__version__)
def cli(filename, laur, names, y, r, model_names, best, method, theta0, only_first, only_a, no_polytomy, compact, parallel, test, debug):
    """Hybridization Models Maximum Likelihood Estimator

    Author: Konstantin Chukharev (lipen00@gmail.com)
    """

    if debug:
        for arg, value in list(locals().items())[::-1]:
            log_debug('{} = {}'.format(arg, value))

    if test:
        filename = None
        names = 'Dog Cow Horse Bat'
        y = '22 21 7 11 14 12 18 16 17 24'
        model_names = all_models
        if compact:
            log_info('Running in test mode...')
        else:
            log_info('Running in test mode equivalent to the following invocation:\n'
                     '$ hammlet --names {} -y {} {}'
                     .format(names, y, ' '.join(map(lambda m: '-m {}'.format(m), model_names))))
        names = tuple(names.split())
        y = tuple(map(int, y.split()))
    elif laur:
        log_info('Using laurasiatherian preset data')
        names = tuple('Dog Cow Horse Bat'.split())
        y = tuple(map(int, '22 21 7 11 14 12 18 16 17 24'.split()))

    species, data = parse_input(filename, names, y, verbose=not compact)
    if not compact:
        print_data(data)
        print_species(species)

    if len(theta0) == 0:
        theta0 = (0.6 * sum(data.values()), 0.5, 0.5, 0.5, 0.5)
        if debug:
            log_debug('Default theta0: {}'.format(theta0))

    if only_a:
        log_info('Doing only a_ij calculations...')
        time_start = time.time()

        for model_name in model_names:
            model_func = get_model_func(model_name)
            a = get_a(model_func, theta0, r)
            print_results(a, data, model_name, theta0, r)

        time_total = time.time() - time_start
        log_success('Done in {:.1f} s.'.format(time_total))
    else:
        log_info('Doing calculations (method: {})...'.format(method))
        time_start = time.time()

        for model_name in model_names:
            click.echo('=' * 70)
            log_info('Optimizing model {}...'.format(model_name))
            time_solve_start = time.time()

            theta_bounds = get_model_theta_bounds(model_name)
            model_func = get_model_func(model_name)
            options = {'maxiter': 500}

            results = OrderedDict()  # {permutation: result}

            if only_first:
                perms = [tuple(range(len(species)))]
            else:
                perms = permutations(range(len(species)))

            worker = Worker(model_func, data, r, theta0, theta_bounds, method, options)
            if parallel > 1:
                pool = Pool(parallel, Worker.ignore_sigint)
                it = pool.imap(worker, perms)
                pool.close()
            else:
                it = map(worker, perms)

            for permutation, result in it:
                results[permutation] = result
                if debug:
                    log_debug('Permutation [{}] done after {} iterations'
                              .format(", ".join(morph(species, permutation)), result.nit))
                if not result.success:
                    log_error('Optimization for model {} failed on permutation [{}] with message: {}'
                              .format(model_name, ', '.join(morph(species, permutation)), result.message))
                    if debug:
                        log_debug('result:\n{}'.format(result))
                    break
            else:
                time_solve = time.time() - time_solve_start
                log_success('Done optimizing model {} in {:.1f} s.'.format(model_name, time_solve))

            if parallel > 1:
                pool.join()

            assert all(result.success for result in results.values()), "Something gone wrong"

            tmp = sorted(results.items(), key=lambda t: t[1].fun)[:best]
            if tmp:
                if not compact:
                    log_info('Hybridization model {}'.format(model_name))
                for i, (permutation, result) in enumerate(tmp, start=1):
                    fit = -result.fun
                    theta = result.x

                    # Do not print polytomy (all parameters except n0 are zero)
                    if no_polytomy and all(abs(x) < 1e-3 for x in theta[1:]):
                        continue

                    if compact:
                        print_compact(i, model_name, morph(species, permutation), fit, theta)
                    else:
                        a = get_a(model_func, theta, r)
                        print_best(i, best, morph(species, permutation), fit, theta)
                        print_rock(a, data, permutation)

        click.echo('=' * 70)
        time_total = time.time() - time_start
        log_success('All done in {:.1f} s.'.format(time_total))


if __name__ == '__main__':
    cli()
