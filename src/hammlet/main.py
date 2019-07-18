import csv
import itertools
import time
import sys

import click

from .models import models_H1, models_H2, models_mapping_mnemonic, models_hierarchy
from .optimizer import Optimizer
from .parsers import parse_best, parse_input, parse_models
from .printers import (log_br, log_debug, log_info, log_success, log_warn, print_a, print_input,
                       print_model_results, print_permutation, print_model_result_boot)
from .utils import get_a, get_chains, morph4
from .version import version as __version__


@click.command(context_settings=dict(
    max_content_width=999,
    help_option_names=['-h', '--help'],
))
@click.option('--preset', metavar='<preset>',
              help='Preset data (laur/12-200/12-200-70-50/5-10/29-8...)')
@click.option('-i', '--input', 'input_filename', metavar='<path|->',
              type=click.Path(exists=True, allow_dash=True),
              help='File with markers presence/absence data')
@click.option('-n', '--names', nargs=4, metavar='<name...>',
              help='Space-separated list of ' + click.style('four', bold=True) + ' species names')
@click.option('-y', nargs=10, metavar='<int...>', type=int,
              help='Space-separated list of ' + click.style('ten', bold=True) +
              ' y values (y11 y12 y13 y14 y22 y23 y24 y33 y34 y44)')
@click.option('-r', nargs=4, metavar='<float...>', type=float,
              default=(1, 1, 1, 1), show_default=True,
              help='Space-separated list of ' + click.style('four', bold=True) + ' r values')
@click.option('-m', '--model', 'models', multiple=True, metavar='<name...|all>', callback=parse_models,
              help='Comma-separated list of models')
@click.option('--theta', nargs=5, type=float, metavar='<n0 T1 T3 g1 g3>',
              help='Space-separated list of ' + click.style('five', bold=True) +
              ' theta components for a_ij (n0 T1 T3 gamma1 gamma3)')
@click.option('--chain', type=click.Choice(['H1', 'H2']),
              help='Model group for simplest models computation')
@click.option('--levels', 'levels_filename', metavar='<path|->',
              type=click.Path(exists=True, allow_dash=True),
              help='File with levels data')
@click.option('--best', 'number_of_best', metavar='<int|all>', callback=parse_best,
              default='all', show_default=True,
              help='Number of best models to show')
@click.option('--method', type=click.Choice(['SLSQP', 'L-BFGS-B', 'TNC']),
              default='SLSQP', show_default=True,
              help='Optimization method')
@click.option('--theta0', nargs=5, type=float, metavar='<n0 T1 T3 g1 g3>',
              help='Space-separated list of ' + click.style('five', bold=True) +
              ' initial theta components (n0 T1 T3 gamma1 gamma3)')
@click.option('--only-first', 'is_only_first', is_flag=True,
              help='Do calculations only for first (initial) permutation')
@click.option('--only-permutation', nargs=4, metavar='<name...>',
              help='Do calculations only for given permutation')
@click.option('--free-permutation', 'is_free_permutation', is_flag=True,
              help='[chain] Use best permutations for each simpler model')
@click.option('--only-a', 'is_only_a', is_flag=True,
              help='Do only a_ij calculations')
@click.option('--bootstrap', 'bootstrap_times', type=int, metavar='<int>',
              default=0, show_default=False,
              help='Bootstrap a_ij values by applying Poisson to the input ys')
@click.option('--no-polytomy', 'is_no_polytomy', is_flag=True,
              help='Do not show polytomy results')
@click.option('--show-permutation', nargs=4, metavar='<name...>',
              help='Show morphed y values for given permutation')
@click.option('-p', '--pvalue', type=float, metavar='<float>',
              default=0.05, show_default=True,
              help='p-value for statistical tests')
@click.option('--debug', is_flag=True,
              help='Debug.')
@click.version_option(__version__)
def cli(preset, input_filename, names, y, r, models, theta, chain, levels_filename,
        number_of_best, method, theta0, is_only_first, only_permutation, is_free_permutation, is_only_a,
        bootstrap_times, is_no_polytomy, show_permutation, pvalue, debug):
    """Hybridization Models Maximum Likelihood Estimator

    Author: Konstantin Chukharev (lipen00@gmail.com)
    """

    # TODO: welcome
    time_start = time.time()

    if debug:
        for arg, value in list(locals().items())[::-1]:
            log_debug('{} = {}'.format(arg, value))

    species, ys = parse_input(preset, input_filename, names, y, verbose=True, is_only_a=is_only_a)
    print_input(species, ys)
    del preset, input_filename, names, y

    if not theta:
        theta = (round(0.6 * sum(ys), 5), 0.5, 0.5, 0.5, 0.5)
        if debug:
            log_debug('Using default theta: {}'.format(theta0))

    if not theta0:
        theta0 = (round(0.6 * sum(ys), 5), 0.5, 0.5, 0.5, 0.5)
        if debug:
            log_debug('Using default theta0: {}'.format(theta0))

    if show_permutation:
        if set(show_permutation) != set(species):
            raise click.BadParameter('must be equal to species ({})'.format(', '.join(species)),
                                     param_hint='show_permutation')

        log_br()
        print_permutation(species, ys, show_permutation)
    elif chain:
        log_br()
        log_info('Searching for simplest models from {}...'.format(chain))
        time_start_chain = time.time()

        if models:
            log_warn('Ignoring specified models due to --chain flag!')

        if chain == 'H1':
            models = models_H1
        else:
            models = models_H2
        hierarchy = models_hierarchy[chain]['free' if is_free_permutation else 'non-free']

        optimizer = Optimizer(species, ys, theta0, r, method, debug=debug)
        if is_only_first:
            perms = [None]
        elif only_permutation:
            perms = [tuple(species.index(s) for s in only_permutation)]
        else:
            perms = list(itertools.permutations(range(len(species))))

        results = {}  # {model_name: (perm, result)}
        if is_free_permutation:
            for model in models:
                res = optimizer.many_perms(model, perms)  # {perm: result}
                best_perm, best_result = max(res.items(), key=lambda t: -t[1].fun)
                results[model.name] = (best_perm, best_result)
                if debug:
                    print_model_results(model, species, {best_perm: best_result}, 1)
        else:
            model_complex = models[0]
            results_complex = optimizer.many_perms(model_complex, perms)  # {perm: result}
            best_complex_perm, best_complex_result = max(results_complex.items(),
                                                         key=lambda t: -t[1].fun)  # (perm, result)
            results[model_complex.name] = (best_complex_perm, best_complex_result)
            if debug:
                log_debug('Best complex permutation: [{}]'.format(', '.join(morph4(species, best_complex_perm))))
            for m, res in optimizer.many_models(models[1:], best_complex_perm).items():
                results[m] = (best_complex_perm, res)
                if debug:
                    print_model_results(m, species, {best_complex_perm: res}, 1)

        chains = get_chains(results, models, hierarchy, pvalue)  # [path::[model_name]]
        log_info('Total {} chain(s):'.format(len(chains)))
        for path in chains:
            log_debug(' -> '.join(path), symbol='chain')

        simplest = sorted(set(p[-1] for p in chains))
        log_success('Done calculating {} simplest model(s) in {:.1f} s.'
                    .format(len(simplest), time.time() - time_start_chain))
        for m in simplest:
            perm, result = results[m]
            print_model_results(m, species, {perm: result}, 1)
    # if show_permutation
    # elif chain
    elif levels_filename:
        log_br()
        log_info('Processing levels...'.format())
        time_start_levels = time.time()

        if models:
            log_warn('Ignoring specified models due to --levels flag!')

        def parse_perm(perm):
            if perm.startswith('{') or perm.startswith('('):
                perm = perm[1:]
            if perm.endswith('}') or perm.endswith(')'):
                perm = perm[:-1]
            return tuple(int(s) - 1 for s in perm.split(','))

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
                model = models_mapping_mnemonic[row['Branch']][row['Case']]
                if model.name != row['Type']:
                    log_warn('Model name mismatch: model.name={}, Type={}'.format(model.name, row['Type']))
                perm = parse_perm(row['Permut'])
                levels_data[level].append((model, perm))

        # ================
        from .models import all_models
        missed_models = set(all_models) - set(model for (model, perm) in sum(levels_data.values(), []))
        if missed_models:
            log_warn('Missed models:')
            for model in missed_models:
                log_warn(' -  {}'.format(model), symbol=None)
        # ================

        log_info('Optimizing...')
        optimizer = Optimizer(species, ys, theta0, r, method, debug=debug)
        levels_results = {level: [] for level in levels_data}  # {level: [(model, perm, result)]}
        for (level, data) in levels_data.items():
            for (model, perm) in data:
                result = optimizer.one(model, perm)
                levels_results[level].append((model, perm, result))
                print_model_results(model, species, {perm: result}, 1)
        levels_best = {level: min(results, key=lambda t: t[2].fun)
                       for level, results in levels_results.items()}

        log_info('Best on levels 4-0:')
        for level in [4, 3, 2, 1, 0]:
            (model, perm, result) = levels_best[level]
            print_model_results(model, species, {perm: result}, 1)

        log_info('Calculating chains...')
        level = 4
        last_accepted = levels_best[level]
        while level > 0:
            (model_complex, perm_complex, result_complex) = last_accepted
            (model_simple, perm_simple, result_simple) = levels_best[level - 1]
            LLcomplex = -result_complex.fun
            LLsimple = -result_simple.fun
            log_debug('Complex model {} has LL={:.3f}, simple model {} has LL={:.3f}'
                      .format(model_complex, LLcomplex, model_simple, LLsimple))
            stat = 2 * (LLcomplex - LLsimple)
            from scipy.special import chdtri
            crit = chdtri(1, pvalue)
            if stat < crit:
                level -= 1
                last_accepted = (model_simple, perm_simple, result_simple)
                log_debug('Accepting simple model {}'.format(model_simple))
            else:
                break

        log_br()
        log_info('Last accepted level: {}'.format(level))
        model, perm, result = last_accepted
        print_model_results(model, species, {perm: result}, 1)

        log_success('Done calculating levels in {:.1f} s.'
                    .format(time.time() - time_start_levels))
    # if show_permutation
    # elif chain
    # elif levels_filename
    else:
        if not models:
            raise click.BadParameter('no models specified', param_hint='models')

        if only_permutation and set(only_permutation) != set(species):
            raise click.BadParameter('must be equal to species ({})'.format(', '.join(species)), param_hint='only_permutation')

        if is_only_a:
            log_br()
            log_info('Doing only a_ij calculations...')

            if is_only_first:
                perm = None
            elif only_permutation:
                perm = tuple(species.index(s) for s in only_permutation)
            else:
                perm = None

            for model in models:
                theta_ = model.apply_bounds(theta)
                a = get_a(model, theta_, r)
                log_success('a_ij for model {} ({}), permutation [{}], theta={}, r={}:'
                            .format(model.name, model.mnemonic_name,
                                    ', '.join(morph4(species, perm)),
                                    '(' + ','.join(str(x).rstrip('0').rstrip('.') for x in theta_) + ')',
                                    '(' + ','.join(str(x).rstrip('0').rstrip('.') for x in r) + ')'))
                print_a(a)

                if debug:
                    optimizer = Optimizer(species, ys, theta0, r, method, debug=debug)
                    result = optimizer.one(model, perm)
                    log_debug('result:\n{}'.format(result), symbol=None)
        # if is_only_a
        else:
            optimizer = Optimizer(species, ys, theta0, r, method, debug=debug)
            if is_only_first:
                perms = [None]
            elif only_permutation:
                perms = [tuple(species.index(s) for s in only_permutation)]
            else:
                perms = list(itertools.permutations(range(len(species))))

            for model in models:
                log_br()
                log_info('Optimizing model {} ({})...'.format(model.name, model.mnemonic_name))
                time_start_optimize = time.time()

                results = optimizer.many_perms(model, perms)  # {perm: result}

                log_success('Done optimizing model {} ({}) in {:.1f} s.'
                            .format(model.name, model.mnemonic_name, time.time() - time_start_optimize))
                # print_model_results(model, species, results, number_of_best, poisson_times, is_no_polytomy)
                print_model_results(model, species, results, number_of_best, 0, is_no_polytomy)

                if bootstrap_times > 0:
                    log_info('Bootstraping best result {} times...'.format(bootstrap_times))
                    best_perm = sorted(results.items(), key=lambda t: t[1].fun)[0][0]
                    from numpy.random import poisson
                    for _ in range(bootstrap_times):
                        ys_poissoned = [poisson(y) for y in ys]
                        optimizer_boot = Optimizer(species, ys_poissoned, theta0, r, method, debug=debug)
                        result_boot = optimizer_boot.one(model, best_perm)
                        print_model_result_boot(model, species, ys_poissoned, best_perm, result_boot)

    log_br()
    log_success('All done in {:.1f} s.'.format(time.time() - time_start))


if __name__ == '__main__':
    cli()
