__all__ = ('log_debug', 'log_info', 'log_success', 'log_warn', 'log_error',
           'print_data', 'print_species', 'print_results', 'print_compact', 'print_best', 'print_rock')

import click

from .utils import fix, pattern2ij


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


def print_data(data):
    log_info('Data:')
    click.secho('  pattern ij  y_ij', bold=True)
    for pattern, y_ij in sorted(data.items(), key=lambda t: pattern2ij(t[0])):
        i, j = pattern2ij(pattern)
        click.echo('    {}  {}{}  {: >3}'.format(pattern, i, j, y_ij))


def print_species(species):
    log_info('{} species: {}'
             .format(len(species), ", ".join(species)))


def print_results(a, data, model, theta, r):
    log_success('Result for hybridization model {} with theta = {}, r = {}:'
                .format(model, theta, r))
    click.secho('  pattern ij  y_ij  a_ij', bold=True)
    for pattern in sorted(a, key=lambda p: pattern2ij(p)):
        a_ij = a[pattern]
        y_ij = data[pattern]
        i, j = pattern2ij(pattern)
        click.echo('    {}  {}{}  {: >3}  {: >6.3f}'
                   .format(pattern, i, j, y_ij, a_ij))


def print_compact(i, model, species, fit, theta):
    n0, T1, T3, gamma1, gamma3 = theta
    log('{}, {}, {}, LL={:.3f}, n0={:.3f}, T1={:.3f}, T3={:.3f}, g1={:.3f}, g3={:.3f}'
        .format(model, i, ', '.join(species), fit, n0, T1, T3, gamma1, gamma3),
        symbol='@')


def print_best(i, best, species, fit, theta):
    n0, T1, T3, gamma1, gamma3 = theta
    log_info('Best #{} of {}'.format(i, best))
    click.echo(click.style(' -   perm:', bold=True) + ' {}'.format(", ".join(species)))
    click.echo(click.style(' -    fit:', bold=True) + ' {:.3f}'.format(fit))
    click.echo(click.style(' -     n0:', bold=True) + ' {:.3f}'.format(n0))
    click.echo(click.style(' -     T1:', bold=True) + ' {:.4f}'.format(T1))
    click.echo(click.style(' -     T3:', bold=True) + ' {:.4f}'.format(T3))
    click.echo(click.style(' - gamma1:', bold=True) + ' {:.4f}'.format(gamma1))
    click.echo(click.style(' - gamma3:', bold=True) + ' {:.4f}'.format(gamma3))


def print_rock(a, data, permutation):
    log_info('For those about to rock:')
    click.secho('  pattern ij  y_ij  a_ij', bold=True)
    for pattern, y_ij in sorted(data.items(), key=lambda t: pattern2ij(fix(t[0], permutation))):
        pattern = fix(pattern, permutation)
        a_ij = a[pattern]
        i, j = pattern2ij(pattern)
        click.echo('    {}  {}{}  {: >3}  {: >6.3f}'
                   .format(pattern, i, j, y_ij, a_ij))
