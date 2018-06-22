__all__ = ('log_debug', 'log_info', 'log_success', 'log_warn', 'log_error', 'log_br',
           'print_input', 'print_permutation', 'print_a', 'print_model_results', 'print_model_best_result')

import click

from .utils import morph4, morph10


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
    log(' '.join('=' * 30), symbol=None, fg=fg, bg=bg, bold=bold, nl=nl)


def print_input(species, ys):
    log_info('Species: ' + ', '.join(species))
    log_info('y values: ' + ' '.join(map(str, ys)))


def print_permutation(species, ys, permutation):
    perm = tuple(species.index(s) for s in permutation)
    ys_ = morph10(ys, perm)
    log('{}, {}'.format(', '.join(permutation), ', '.join(map(str, ys_))), symbol='@')


def print_a(a, ys, perm):
    ij = [(i + 1, j + 1) for i in range(4) for j in range(i, 4)]
    ij_ = morph10(ij, perm)
    ys_ = morph10(ys, perm)
    log(' ij  y_ij ~ij~~y_ij~  a_ij', symbol=None, bold=True)
    for (i, j), y_ij, (i_, j_), y_ij_, a_ij in zip(ij, ys, ij_, ys_, a):
        log(' {}{}  {:>3}   {}{}  {:>3}  {:>7.3f}'.format(i, j, y_ij, i_, j_, y_ij_, a_ij), symbol=None)


def print_model_results(model, species, results, number_of_best, is_no_polytomy=False):
    best_results = sorted(results.items(), key=lambda t: t[1].fun)[:number_of_best]
    for i, (perm, result) in enumerate(best_results, start=1):
        fit = -result.fun
        theta = result.x
        n0, T1, T3, gamma1, gamma3 = theta
        # Do not print polytomy (when all parameters except n0 are near to zero)
        if is_no_polytomy and all(abs(x) < 1e-3 for x in (T1, T3, gamma1, gamma3)):
            continue
        log('{}, {}, {}, LL={:.3f}, n0={:.3f}, T1={:.3f}, T3={:.3f}, g1={:.3f}, g3={:.3f}'
            .format(model, i, ', '.join(morph4(species, perm)), fit, n0, T1, T3, gamma1, gamma3),
            symbol='@')


def print_model_best_result(model, result):
    fit = -result.fun
    theta = result.x
    n0, T1, T3, gamma1, gamma3 = theta
    log('{}, LL={:.3f}, n0={:.3f}, T1={:.3f}, T3={:.3f}, g1={:.3f}, g3={:.3f}'
        .format(model, fit, n0, T1, T3, gamma1, gamma3),
        symbol='@')
