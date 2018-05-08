__all__ = ('log_debug', 'log_info', 'log_success', 'log_warn', 'log_error', 'log_br',
           'print_input', 'print_compact', 'print_best', 'print_a')

import click

from .utils import morph10


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


def print_compact(i, model, species, fit, theta):
    n0, T1, T3, gamma1, gamma3 = theta
    log('{}, {}, {}, LL={:.3f}, n0={:.3f}, T1={:.3f}, T3={:.3f}, g1={:.3f}, g3={:.3f}'
        .format(model, i, ', '.join(species), fit, n0, T1, T3, gamma1, gamma3),
        symbol='@')


def print_best(i, species, fit, theta):
    n0, T1, T3, gamma1, gamma3 = theta
    log_info('Best #{}'.format(i))
    click.echo(click.style(' -   perm:', bold=True) + ' {}'.format(', '.join(species)))
    click.echo(click.style(' -    fit:', bold=True) + ' {:.3f}'.format(fit))
    click.echo(click.style(' -     n0:', bold=True) + ' {:.3f}'.format(n0))
    click.echo(click.style(' -     T1:', bold=True) + ' {:.4f}'.format(T1))
    click.echo(click.style(' -     T3:', bold=True) + ' {:.4f}'.format(T3))
    click.echo(click.style(' - gamma1:', bold=True) + ' {:.4f}'.format(gamma1))
    click.echo(click.style(' - gamma3:', bold=True) + ' {:.4f}'.format(gamma3))


def print_a(a, ys, perm):
    ij = [(i + 1, j + 1) for i in range(4) for j in range(i, 4)]
    ij_ = morph10(ij, perm)
    ys_ = morph10(ys, perm)
    log(' ij  y_ij ~ij~~y_ij~  a_ij', symbol=None, bold=True)
    for (i, j), y_ij, (i_, j_), y_ij_, a_ij in zip(ij, ys, ij_, ys_, a):
        log(' {}{}  {:>3}   {}{}  {:>3}  {:>7.3f}'.format(i, j, y_ij, i_, j_, y_ij_, a_ij), symbol=None)
