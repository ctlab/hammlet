import time
from multiprocessing import Pool
from itertools import permutations
from collections import OrderedDict

import click
import numpy as np

from .utils import *
from .printers import *
from version import get_version


def parse_input(filename, names, y):
    if filename:
        log_info(f'Reading data from <{filename}>...')
        with click.open_file(filename) as f:
            lines = f.read().strip().split('\n')
            assert len(lines) >= 11, "File must contain header with names and 10 rows of data (patterns and y values)"

        species = lines[0].strip().split()[:-1]
        data = OrderedDict()  # {pattern: y_ij}
        for line in lines[1:]:
            tmp = line.strip().split()
            pattern = ''.join(tmp[:-1])
            assert set(pattern) == set('+-'), "Weird symbols in pattern"
            y_ij = int(tmp[-1])
            data[pattern] = y_ij
    else:
        if not y:
            raise click.BadParameter('missing y values')
        species = names
        data = OrderedDict()  # {pattern: y_ij}
        ys = iter(y)
        for i in range(4):
            for j in range(i, 4):
                pattern = ij2pattern(i + 1, j + 1)
                data[pattern] = next(ys)
    return species, data


def parse_models(ctx, param, value):
    if len(value) == 0 or 'all' in value:
        return ('2H1', '2H2')
    else:
        assert all(map(get_model_func, value)), "Unknown model name (or anything else...)"
        return value


def parse_best(ctx, param, value):
    if value == 'all':
        return value
    try:
        return int(value)
    except ValueError:
        raise click.BadParameter('best need to be a number or "all"')


@click.command(context_settings=dict(
    max_content_width=999,
))
@click.option('-i', '--input', 'filename', type=click.Path(exists=True, allow_dash=True),
              help='File with markers presence/absence data')
# FIXME: add meta = <4 names>
@click.option('-n', '--names', nargs=4,
              default=('Name1', 'Name2', 'Name3', 'Name4'),
              help='Space-separated list of ' + click.style('four', bold=True) + ' species names')
@click.option('-y', nargs=10, type=int,
              help='Space-separated list of ' + click.style('ten', bold=True) + ' y values (y11 y12 y13 y14 y22 y23 y24 y33 y34 y44)')
@click.option('-r', nargs=4, type=float,
              default=(1, 1, 1, 1), show_default=True,
              help='Space-separated list of ' + click.style('four', bold=True) + ' r values')
@click.option('-m', '--model', 'model_names', multiple=True, callback=parse_models,
              help='Which model to use. Pass multiple times to use many models. Pass "all" to use all available models (default behaviour)')
@click.option('--best', callback=parse_best,
              default='all', show_default=True,
              help='Number of best models to show')
@click.option('--method', type=click.Choice(['SLSQP', 'L-BFGS-B', 'TNC']),
              default='SLSQP', show_default=True,
              help='Optimization method')
@click.option('--theta0', nargs=5, type=float,
              help='Space-separated list of ' + click.style('five', bold=True) + ' initial theta components (n0 T1 T3 gamma1 gamma3)')
@click.option('--only-first', is_flag=True,
              help='Do calculations only for first (initial) permutation')
@click.option('--only-a', is_flag=True,
              help='Do only a_ij calculations')
@click.option('-p', '--parallel', type=int,
              default=1, show_default=True,
              help='Number of parallel optimizing processes')
@click.option('--test', is_flag=True,
              help='Run test')
@click.option('--debug', is_flag=True,
              help='Debug')
@click.version_option(get_version())
def cli(filename, names, y, r, model_names, best, method, theta0, only_first, only_a, parallel, test, debug):
    """Hybridization Networks Maximum Likelihood Estimator"""

    if debug:
        for arg, value in list(locals().items())[::-1]:
            log_debug(f'{arg} = {value}')

    if test:
        filename = None
        names = tuple('Dog Cow Horse Bat'.split())
        y = tuple(map(int, '17 18 12 11 7 21 24 16 14 22'.split()))
        model_names = tuple('1P1 1P2 1T1 1T2 1PH1 1PH2 1H1 1H2 1H3 1H4 1HP 2H1 '
                            '2P1 2P2 2PH1 2PH2 2T1 2T2 2HP 2HA 2HB 2H2'.split())

    species, data = parse_input(filename, names, y)
    print_data(data)
    print_species(species)

    if len(theta0) == 0:
        theta0 = (0.6 * sum(data.values()), 0.5, 0.5, 0.5, 0.5)
        if debug:
            log_debug(f'Default theta0: {theta0}')

    if only_a:
        log_info('Doing only a_ij calculations...')
        time_start = time.time()

        for model_name in model_names:
            model_func = get_model_func(model_name)
            a = get_all_a(model_func, None, theta0, r)
            print_results(a, data, model_name, theta0, r)

        time_total = time.time() - time_start
        log_success(f'Done in {time_total:.1f} s.')
    else:
        log_info(f'Doing calculations (method: {method})...')
        time_start = time.time()

        a_hat = sum(data.values()) / 10
        L0 = 10 * a_hat * (np.log(a_hat) - 1)
        if debug:
            log_debug(f'a_hat: {a_hat:.3f}')
            log_debug(f'L_0: {L0:.3f}')

        for model_name in model_names:
            click.echo('=' * 70)
            log_info(f'Optimizing model {model_name}...')
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
                    log_debug(f'Permutation [{", ".join(fix(species, permutation))}] done after {result.nit} iterations')
                if not result.success:
                    log_error(f'Optimization for model {model_name} failed on permutation [{", ".join(fix(species, permutation))}] with message: {result.message}')
                    if debug:
                        log_debug(f'result:\n{result}')
                    break
            else:
                time_solve = time.time() - time_solve_start
                log_success(f'Done optimizing model {model_name} in {time_solve:.1f} s.')

            if parallel > 1:
                pool.join()

            assert all(result.success for result in results.values()), 'Something gone wrong'

            tmp = sorted(results.items(), key=lambda t: t[1].fun)
            if isinstance(best, int):
                tmp = tmp[:best]

            log_info(f'Hybridization model {model_name}')
            for i, (permutation, result) in enumerate(tmp, start=1):
                fit = -result.fun
                ratio = 2 * (fit - L0)
                n0, T1, T3, gamma1, gamma3 = result.x
                print_best(i, best, fix(species, permutation), fit, ratio, n0, T1, T3, gamma1, gamma3)

                a = get_all_a(model_func, permutation, result.x, r)
                print_rock(a, data, model_name, permutation, result.x, r)

        click.echo('=' * 70)
        time_total = time.time() - time_start
        log_success(f'All done in {time_total:.1f} s.')


if __name__ == '__main__':
    cli()
