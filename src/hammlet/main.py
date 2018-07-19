import itertools
import time

import click

from .models import models_H1, models_H2
from .optimizer import Optimizer
from .parsers import parse_best, parse_input, parse_models
from .printers import (log_br, log_debug, log_info, log_success, log_warn, print_a, print_input,
                       print_model_results, print_permutation)
from .utils import get_a, get_chains, morph4
from .version import version as __version__


@click.command(context_settings=dict(
    max_content_width=999,
    help_option_names=['-h', '--help'],
))
@click.option('--preset', metavar='<preset>',
              help='Preset data (laur/hctm/12-200/12-200-70-50/5-10/...)')
@click.option('-i', '--input', 'filename', metavar='<path|->',
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
@click.option('--chain', type=click.Choice(['H1', 'H2']),
              help='Model group for simplest models computation')
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
def cli(preset, filename, names, y, r, models, chain, number_of_best, method, theta0, is_only_first, only_permutation, is_free_permutation, is_only_a, is_no_polytomy, show_permutation, pvalue, debug):
    """Hybridization Models Maximum Likelihood Estimator

    Author: Konstantin Chukharev (lipen00@gmail.com)
    """

    # TODO: welcome
    time_start = time.time()

    if debug:
        for arg, value in list(locals().items())[::-1]:
            log_debug('{} = {}'.format(arg, value))

    species, ys = parse_input(preset, filename, names, y, verbose=True, is_only_a=is_only_a)
    print_input(species, ys)
    del preset, filename, names, y

    if not theta0:
        theta0 = (round(0.6 * sum(ys), 5), 0.5, 0.5, 0.5, 0.5)
        if debug:
            log_debug('Using default theta0: {}'.format(theta0))

    if show_permutation:
        if set(show_permutation) != set(species):
            raise click.BadParameter('must be equal to species ({})'.format(', '.join(species)), param_hint='show_permutation')

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
            if is_free_permutation:
                hierarchy = {
                    '2H1': '1H1 1H2 1H3 1H4 1HP'.split(),
                    '1H1': '1T1 1T2 1PH1 1PH2 1PH3'.split(),
                    '1H2': '1T1 1T2 1PH1 1PH2 1PH3'.split(),
                    '1H3': '1T1 1T2 1PH1 1PH2 1PH3'.split(),
                    '1H4': '1T1 1T2 1PH1 1PH2 1PH3'.split(),
                    '1HP': '1T1 1T2 1PH1 1PH2 1PH3'.split(),
                    '1T1': '1P1 1P2 1P3'.split(),
                    '1T2': '1P1 1P2 1P3'.split(),
                    '1PH1': '1P1 1P2 1P3'.split(),
                    '1PH2': '1P1 1P2 1P3'.split(),
                    '1PH3': '1P1 1P2 1P3'.split(),
                    '1P1': 'PL1'.split(),
                    '1P2': 'PL1'.split(),
                    '1P3': 'PL1'.split(),
                }
            else:
                hierarchy = {
                    '2H1': '1H1 1H2 1H3 1H4 1HP 1PH1'.split(),
                    '1H1': '1T1 1T2 1P1 1PH2'.split(),
                    '1H2': '1PH1 1T2B 1T1 1PH1A'.split(),
                    '1H3': '1T2A 1T2 1PH1 1P2'.split(),
                    '1H4': '1T2B 1T2A 1PH3 1P2A'.split(),
                    '1HP': 'PL1 1P2 1PH2 1PH3 1PH1A'.split(),
                    '1T1': '1P1 1P3'.split(),
                    '1T2': '1P1 1P2'.split(),
                    '1T2A': '1P2 1P2A'.split(),
                    '1T2B': '1P2A 1P2B'.split(),
                    '1PH1': '1P2A PL1'.split(),
                    '1PH1A': '1P2B 1P3 PL1'.split(),
                    '1PH2': '1P2 1P3 PL1'.split(),
                    '1PH3': '1P2 1P2B PL1'.split(),
                    '1P1': 'PL1'.split(),
                    '1P2': 'PL1'.split(),
                    '1P2A': 'PL1'.split(),
                    '1P2B': 'PL1'.split(),
                    '1P3': 'PL1'.split(),
                }
        elif chain == 'H2':
            models = models_H2
            if is_free_permutation:
                hierarchy = {
                    '2H2': '2HA1 2HB1 2HP'.split(),
                    '2HA1': '2T1 2T2 2PH1 2PH2'.split(),
                    '2HB1': '2T1 2T2 2PH1 2PH2'.split(),
                    '2HP': '2T1 2T2 2PH1 2PH2'.split(),
                    '2T1': '2P1 2P2 2P3'.split(),
                    '2T2': '2P1 2P2 2P3'.split(),
                    '2PH1': '2P1 2P2 2P3'.split(),
                    '2PH2': '2P1 2P2 2P3'.split(),
                    '2P1': 'PL2'.split(),
                    '2P2': 'PL2'.split(),
                    '2P3': 'PL2'.split(),
                }
            else:
                hierarchy = {
                    '2H2': '2HA1 2HA2 2HB1 2HB2 2HP'.split(),
                    '2HA1': '2PH2 2T2 2T1'.split(),
                    '2HA2': '2P1A 2T2B 2T2A 2PH2C'.split(),
                    '2HB1': '2T2A 2PH1 2PH2B 2PH2A'.split(),
                    '2HB2': '2T1 2T2B 2PH1 2PH2B'.split(),
                    '2HP': '2PH2 2PH2A 2PH2B 2PH2C PL2'.split(),
                    '2T1': '2P3 2P1'.split(),
                    '2T2': '2P1 2P2'.split(),
                    '2T2A': '2P1A 2P3A'.split(),
                    '2T2B': '2P1A 2P2A'.split(),
                    '2PH1': '2P1 2P1A PL2'.split(),
                    '2PH2': '2P2 2P3 PL2'.split(),
                    '2PH2A': '2P2 2P3A PL2'.split(),
                    '2PH2B': '2P1 2P3'.split(),
                    '2PH2C': '2P2A 2P3A'.split(),
                    '2P1': 'PL2'.split(),
                    '2P1A': 'PL2'.split(),
                    '2P2': 'PL2'.split(),
                    '2P2A': 'PL2'.split(),
                    '2P3': 'PL2'.split(),
                    '2P3A': 'PL2'.split(),
                }
        else:
            raise NotImplementedError('unsupported chain "{}"'.format(chain))

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

        chains = get_chains(results, models, hierarchy, pvalue)
        log_info('Total {} chain(s):'.format(len(chains)))
        for path in chains:
            log_debug('    ' + ' -> '.join(path), symbol=None)

        simplest = sorted(set(p[-1] for p in chains))
        log_success('Done calculating {} simplest model(s) in {:.1f} s.'
                    .format(len(simplest), time.time() - time_start_chain))
        for m in simplest:
            perm, result = results[m]
            print_model_results(m, species, {perm: result}, 1)
    # if show_permutation
    # elif chain
    else:
        if len(models) == 0:
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
                a = get_a(model, theta0, r)
                log_success('Result for model {}, permutation [{}], theta={}, r={}:'
                            .format(model, ', '.join(morph4(species, perm)), theta0, r))
                print_a(a, ys, perm)

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
                log_info('Optimizing model {}...'.format(model))
                time_start_optimize = time.time()

                results = optimizer.many_perms(model, perms)  # {perm: result}

                log_success('Done optimizing model {} in {:.1f} s.'
                            .format(model, time.time() - time_start_optimize))
                print_model_results(model, species, results, number_of_best, is_no_polytomy)

    log_br()
    log_success('All done in {:.1f} s.'.format(time.time() - time_start))


if __name__ == '__main__':
    cli()
