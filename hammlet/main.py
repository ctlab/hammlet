import time
import itertools
from collections import deque, OrderedDict

import click
# from scipy.stats import chi2
from scipy.special import chdtri  # faster

from .utils import *
from .models import *
from .parsers import *
from .printers import *
from .instance import *
from version import __version__


@click.command(context_settings=dict(
    max_content_width=999,
    help_option_names=['-h', '--help'],
))
@click.option('--preset', metavar='<preset>',
              help='Preset data (laur/12-200/12-200-70-50/...)')
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
@click.option('-m', '--model', 'models', multiple=True, metavar='<int...|all>', callback=parse_models,
              help='Comma-separated list of models to do calculations for. '
                   'Pass "all" to use all available models')
@click.option('--chain', type=click.Choice(['H1', 'H2']),
              help='Chain.')
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
@click.option('--only-a', 'is_only_a', is_flag=True,
              help='Do only a_ij calculations')
@click.option('--no-polytomy', 'is_no_polytomy', is_flag=True,
              help='Do not show polytomy results')
@click.option('--show-permutation', nargs=4, metavar='<name...>',
              help='Show morphed y`s for given permutation')
@click.option('-p', '--pvalue', type=float, metavar='<float>',
              default=0.05, show_default=True,
              help='p-value for statistical tests')
@click.option('--debug', is_flag=True,
              help='Debug.')
@click.version_option(__version__)
def cli(preset, filename, names, y, r, models, chain, number_of_best, method, theta0, is_only_first, only_permutation, is_only_a, is_no_polytomy, show_permutation, pvalue, debug):
    """Hybridization Models Maximum Likelihood Estimator

    Author: Konstantin Chukharev (lipen00@gmail.com)
    """

    # TODO: welcome
    time_start = time.time()

    if debug:
        for arg, value in list(locals().items())[::-1]:
            log_debug('{} = {}'.format(arg, value))

    species, ys = parse_input(preset, filename, names, y, verbose=True)
    print_input(species, ys)
    del preset, filename, names, y

    if len(theta0) == 0:
        theta0 = (round(0.6 * sum(ys), 5), 0.5, 0.5, 0.5, 0.5)
        if debug:
            log_debug('Using default theta0: {}'.format(theta0))

    if show_permutation:
        log_br()
        print_permutation(species, ys, show_permutation)
    elif chain:
        log_br()
        log_info('Doing stuff for chain {}...'.format(chain))
        time_start_chain = time.time()

        if models:
            log_warn('Ignoring specified models due to --chain flag!')

        if chain == 'H1':
            models = models_H1
            hierarchy = {'2H1': '1H1 1H2 1H3 1H4 1HP'.split(),
                         '1H1': '1T1 1T2 1PH2'.split(),  # 1T1 ???
                         '1H2': '1T1 1T2 1PH1'.split(),
                         '1H3': '1T1 1T2 1PH1'.split(),  # 1T1 ???
                         '1H4': '1T1 1T2 1PH2'.split(),  # 1T1, 1PH2 ???
                         '1HP': '1PH2'.split(),
                         '1T1': '1P1 1P2'.split(),
                         '1T2': '1P1 1P2'.split(),
                         '1PH1': '1P1'.split(),
                         '1PH2': '1P2'.split(),
                         '1P1': 'PL1'.split(),
                         '1P2': 'PL1'.split()}
        elif chain == 'H2':
            models = models_H2
            hierarchy = {'2H2': '2HA1 2HA2 2HB1 2HB2 2HP'.split(),
                         '2HA1': '2T1 2T2 2PH2'.split(),
                         '2HA2': '2T1 2T2 2PH2'.split(),
                         '2HB1': '2T1 2T2 2PH1'.split(),
                         '2HB2': '2T1 2T2 2PH1'.split(),
                         '2HP': '2PH2'.split(),
                         '2T1': '2PH1 2PH2'.split(),
                         '2T2': '2PH1 2PH2'.split(),
                         '2PH1': '2P1'.split(),
                         '2PH2': '2P2'.split(),
                         '2P1': 'PL2'.split(),
                         '2P2': 'PL2'.split()}
        else:
            raise NotImplementedError('unsupported chain "{}"'.format(chain))

        model_complex = models[0]
        if debug:
            log_debug('Optimizing complex model {}...'.format(model_complex))
            time_start_optimize_complex = time.time()
        inst_complex = Instance(species=species, ys=ys, model=model_complex,
                                theta0=theta0, r=r, method=method, debug=debug)
        if is_only_first:
            perms = [tuple(ranger(len(species)))]
        elif only_permutation:
            perms = [tuple(species.index(s) for s in only_permutation)]
        else:
            perms = list(itertools.permutations(range(len(species))))
        results_complex = inst_complex.optimize_all(perms)
        best_complex_perm, best_complex_result = max(results_complex.items(), key=lambda t: -t[1].fun)  # (perm, result)
        if debug:
            log_debug('Done optimizing complex model {} in {:.1f} s.'
                      .format(model_complex, time.time() - time_start_optimize_complex))
        log_info('Best complex permutation: {}'
                 .format(', '.join(morph4(species, best_complex_perm))))

        results = OrderedDict()  # {model_name: result}
        results[model_complex.name] = best_complex_result

        if debug:
            log_debug('Optimizing other models...')
            time_start_optimize_other = time.time()
        for model in models:
            if model is model_complex:
                continue
            inst = Instance(species=species, ys=ys, model=model,
                            theta0=theta0, r=r, method=method, debug=debug)
            result = inst.optimize_one(best_complex_perm)
            results[model.name] = result
        if debug:
            log_debug('Done optimizing other models for permutation [{}] in {:.1f} s.'
                      .format(', '.join(morph4(species, best_complex_perm)),
                              time.time() - time_start_optimize_other))
            for m, result in results.items():
                print_model_results(m, species, {best_complex_perm: result}, 1)

        chains = []
        q = deque([[models[0].name]])
        while q:
            path = q.popleft()
            complex = path[-1]  # more complex model
            if complex == models[-1].name:
                chains.append(tuple(path))
            else:
                LLcomplex = -results[complex].fun
                any_child = False
                for simple in hierarchy[complex]:  # more simple model
                    LLsimple = -results[simple].fun
                    stat = (LLcomplex - LLsimple)
                    # crit = 3.841458821  # qchisq(p=0.05, df=1, lower.tail=FALSE)
                    # crit = chi2.ppf(1 - pvalue, 1)
                    crit = chdtri(1, pvalue)  # faster
                    if stat < crit:
                        # log_debug('{}->{}, LLcomplex={:.3f}, LLsimple={:.3f}, stat={:.3f}, extended-path=[{}]'
                        #           .format(complex, simple, LLcomplex, LLsimple, stat, ' '.join(path + [simple])))
                        q.append(path + [simple])
                        any_child = True
                if not any_child:
                    chains.append(tuple(path))

        chains = sorted(set(chains), key=lambda p: (len(p), p))
        if debug:
            log_info('Total {} chains:'.format(len(chains)))
            for path in chains:
                log_debug('    ' + ' -> '.join(path), symbol=None)

        simplest = sorted(set(p[-1] for p in chains))
        log_success('Done calculating {} simplest model(s) in {:.1f} s.'
                    .format(len(simplest), time.time() - time_start_chain))
        for m in simplest:
            print_model_results(m, species, {best_complex_perm: results[m]}, 1)
    # if show_permutation
    # elif chain
    else:
        if len(models) == 0:
            raise click.BadParameter('no models specified', param_hint='models')

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
                    inst = Instance(species=species, ys=ys, model=model,
                                    theta0=theta0, r=r, method=method, debug=debug)
                    result = inst.optimize_one(perm)
                    log_debug('result:\n{}'.format(result), symbol=None)
        # if is_only_a
        else:
            for model in models:
                log_br()
                log_info('Optimizing model {}...'.format(model))
                time_start_optimize = time.time()

                inst = Instance(species=species, ys=ys, model=model,
                                theta0=theta0, r=r, method=method, debug=debug)
                if is_only_first:
                    perms = [None]
                elif only_permutation:
                    perms = [tuple(species.index(s) for s in only_permutation)]
                else:
                    perms = list(itertools.permutations(range(len(species))))
                results = inst.optimize_all(perms)  # {perm: result}

                log_success('Done optimizing model {} in {:.1f} s.'
                            .format(model, time.time() - time_start_optimize))
                print_model_results(model, species, results, number_of_best)

    log_br()
    log_success('All done in {:.1f} s.'.format(time.time() - time_start))


if __name__ == '__main__':
    cli()
