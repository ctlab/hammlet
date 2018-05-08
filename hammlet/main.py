import time

import click

from .parsers import *
from .printers import *
from .utils import *
from .instance import *
from .models import all_models
from version import __version__


@click.command(context_settings=dict(
    max_content_width=999,
    help_option_names=['-h', '--help'],
))
@click.option('-i', '--input', 'filename', metavar='<path|->',
              type=click.Path(exists=True, allow_dash=True),
              help='File with markers presence/absence data')
@click.option('--laur', is_flag=True,
              help='Use laurasiatherian preset data')
@click.option('-n', '--names', nargs=4, metavar='<name...>',
              default=('Name1', 'Name2', 'Name3', 'Name4'),
              help='Space-separated list of ' + click.style('four', bold=True) + ' species names')
@click.option('-y', nargs=10, metavar='<int...>', type=int,
              help='Space-separated list of ' + click.style('ten', bold=True) +
                   ' y values (y11 y12 y13 y14 y22 y23 y24 y33 y34 y44)')
@click.option('-r', nargs=4, metavar='<float...>', type=float,
              default=(1, 1, 1, 1), show_default=True,
              help='Space-separated list of ' + click.style('four', bold=True) + ' r values')
@click.option('-m', '--model', 'models', multiple=True, metavar='<int|all>', callback=parse_models,
              help='Which model to use. Pass multiple times to use many models. '
                   'Pass "all" to use all available models (default behaviour)')
@click.option('--best', 'number_of_best', metavar='<int|all>', callback=parse_best,
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
@click.option('--only-permutation', nargs=4, metavar='<name...>',
              help='Do calculations only for given permutation')
@click.option('--only-a', is_flag=True,
              help='Do only a_ij calculations')
@click.option('--no-polytomy', is_flag=True,
              help='Do not show polytomy results')
@click.option('--compact', is_flag=True,
              help='Compact results (for batch-mode)')
@click.option('--show-permutation', nargs=4, metavar='<name...>',
              help='Show morphed y`s for given permutation')
@click.option('-p', '--parallel', type=int, metavar='<int>',
              default=1, show_default=True,
              help='Number of parallel optimizing processes')
@click.option('--test', is_flag=True,
              help='Run test')
@click.option('--debug', is_flag=True,
              help='Debug')
@click.version_option(__version__)
def cli(filename, laur, names, y, r, models, number_of_best, method, theta0, only_first, only_permutation, only_a, no_polytomy, compact, show_permutation, parallel, test, debug):
    """Hybridization Models Maximum Likelihood Estimator

    Author: Konstantin Chukharev (lipen00@gmail.com)
    """

    time_start = time.time()

    if debug:
        for arg, value in list(locals().items())[::-1]:
            log_debug('{} = {}'.format(arg, value))

    if test:
        if filename:
            log_warn('Ignoring specified filename due to test mode!')
        if names and names != ('Name1', 'Name2', 'Name3', 'Name4'):
            log_warn('Ignoring specified species names due to test mode!')
        if y:
            log_warn('Ignoring specified `y` values due to test mode!')
        if models and set(models) != set(all_models):
            log_warn('Ignoring specified models due to test mode!')
        filename = None
        names = 'Dog Cow Horse Bat'
        y = '22 21 7 11 14 12 18 16 17 24'
        models = all_models
        if compact:
            log_info('Running in test mode...')
        else:
            log_info('Running in test mode equivalent to the following invocation:\n'
                     '$ hammlet --names {} -y {} -m {}'
                     .format(names, y, ','.join(map(str, models))))
        names = tuple(names.split())
        y = tuple(map(int, y.split()))
    elif laur:
        log_info('Using laurasiatherian preset data')
        filename = None
        names = tuple('Dog Cow Horse Bat'.split())
        y = tuple(map(int, '22 21 7 11 14 12 18 16 17 24'.split()))

    species, ys = parse_input(filename, names, y, verbose=not compact)
    if not compact:
        print_input(species, ys)

    if len(theta0) == 0:
        theta0 = (0.6 * sum(ys), 0.5, 0.5, 0.5, 0.5)
        if debug:
            log_debug('Using default theta0: {}'.format(theta0))

    if len(models) == 0:
        raise click.BadParameter('no models specified')

    inst = Instance(
        species=species,
        ys=ys,
        models=models,
        theta0=theta0,
        r=r,
        method=method,
        parallel=parallel,
        compact=compact,
        no_polytomy=no_polytomy,
        number_of_best=number_of_best,
        debug=debug
    )

    if only_first:
        if only_permutation:
            log_warn('Ignoring specified permutation due to --only-first flag')
        only_permutation = inst.species

    if show_permutation:
        if only_permutation:
            log_warn('Only showing permutation without doing calculations due to --show-permutation flag')
        inst.only_show_permutation(show_permutation)
    elif only_a:
        inst.run_only_a(only_permutation)
    else:
        inst.run(only_permutation)

    log_br()
    log_success('All done in {:.1f} s.'.format(time.time() - time_start))


if __name__ == '__main__':
    cli()
