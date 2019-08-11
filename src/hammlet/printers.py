import click

__all__ = ['log_debug', 'log_info', 'log_success', 'log_warn', 'log_error', 'log_br',
           'print_input', 'print_permutation', 'print_a', 'print_model_results']


def log(text, symbol, fg=None, bg=None, bold=None, nl=True):
    if symbol is None:
        pre = ''
    else:
        pre = '[{: >1}] '.format(symbol)
    click.secho('{}{}'.format(pre, text), fg=fg, bg=bg, bold=bold, nl=nl)


def log_debug(text, symbol='.', fg='white', bg=None, bold=None, nl=True):
    log(text, symbol, fg=fg, bg=bg, bold=bold, nl=nl)


def log_info(text, symbol='*', fg='blue', bg=None, bold=True, nl=True):
    log(text, symbol, fg=fg, bg=bg, bold=bold, nl=nl)


def log_success(text, symbol='+', fg='green', bg=None, bold=True, nl=True):
    log(text, symbol, fg=fg, bg=bg, bold=bold, nl=nl)


def log_warn(text, symbol='!', fg='magenta', bg=None, bold=True, nl=True):
    log(text, symbol, fg=fg, bg=bg, bold=bold, nl=nl)


def log_error(text, symbol='!', fg='red', bg=None, bold=True, nl=True):
    log(text, symbol, fg=fg, bg=bg, bold=bold, nl=nl)


def log_br(fg='white', bg=None, bold=False, nl=True):
    log(' '.join('=' * 40), symbol=None, fg=fg, bg=bg, bold=bold, nl=nl)


def print_input(species, ys):
    log_info('Species: ' + ', '.join(species))
    log_info('y values: ' + ' '.join(map(str, ys)))


def print_permutation(species, ys, permutation):
    from .utils import morph10
    perm = tuple(p - 1 for p in permutation)
    ys_ = morph10(ys, perm)
    log('{}, {}'.format(', '.join(map(str, permutation)), ', '.join(map(str, ys_))), symbol='@permutation')


def print_a(a, bootstrap_times=0):
    log(', '.join(map('{:.3f}'.format, a)), symbol='@a_ij')
    if bootstrap_times:
        from numpy.random import poisson
        a = tuple(int(round(a_ij)) for a_ij in a)
        for _ in range(bootstrap_times):
            pa = poisson(a)
            log(', '.join(map(str, pa)), symbol='@poisson')


def print_model_results(model, species, results, number_of_best, poisson_times=0, is_no_polytomy=False):
    from .models import models_mapping
    from .utils import morph4
    if isinstance(model, str):
        model = models_mapping[model]
    best_results = sorted(results.items(), key=lambda t: t[1].fun)[:number_of_best]

    for i, (perm, result) in enumerate(best_results, start=1):
        fit = -result.fun
        theta = result.x
        n0, T1, T3, gamma1, gamma3 = theta
        # Do not print polytomy (when all parameters except n0 are near to zero)
        if is_no_polytomy and all(abs(x) < 1e-3 for x in (T1, T3, gamma1, gamma3)):
            continue
        log('{}, {}, {}, {}, LL={:.3f}, n0={:.3f}, T1={:.3f}, T3={:.3f}, g1={:.3f}, g3={:.3f}'
            .format(model.name, model.mnemonic_name, i, ', '.join(morph4(species, perm)), fit, n0, T1, T3, gamma1, gamma3),
            symbol='@result')

    if poisson_times:
        from .utils import get_a
        best_result = best_results[0][1]
        a = get_a(model, best_result.x, best_result.r)
        log_info('Applying Poisson on the best result:')
        print_a(a, poisson_times)


def print_model_result_boot(model, y, perm, result):
    from .models import models_mapping
    if isinstance(model, str):
        model = models_mapping[model]

    n0, T1, T3, gamma1, gamma3 = result.theta
    log('{}, {}, y=[{}], perm=({}), LL={:.3f}, n0={:.3f}, T1={:.3f}, T3={:.3f}, g1={:.3f}, g3={:.3f}'
        .format(model.name, model.mnemonic_name, ' '.join(map(str, y)), ','.join(map(str, perm)), result.LL, n0, T1, T3, gamma1, gamma3),
        symbol='@boot')


# def print_model_best_result(model, result):
#     fit = -result.fun
#     theta = result.x
#     n0, T1, T3, gamma1, gamma3 = theta
#     log('{}, LL={:.3f}, n0={:.3f}, T1={:.3f}, T3={:.3f}, g1={:.3f}, g3={:.3f}'
#         .format(model, fit, n0, T1, T3, gamma1, gamma3),
#         symbol='@')
