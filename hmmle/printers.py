__all__ = ('log_debug', 'log_info', 'log_success', 'log_warn', 'log_error',
           'print_data', 'print_species', 'print_results', 'print_best', 'print_rock')

import click

from .utils import fix, pattern2ij


def log(text, symbol, *, fg=None, bg=None, bold=None, nl=True):
    if symbol is None:
        pre = ''
    else:
        pre = f'[{symbol: >1}] '
    click.secho(f'{pre}{text}', fg=fg, bg=bg, bold=bold, nl=nl)


def log_debug(text, *, symbol='.', fg='white', bg=None, bold=None, nl=True):
    log(text, symbol, fg=fg, bg=bg, bold=bold, nl=nl)


def log_info(text, *, symbol='*', fg='blue', bg=None, bold=True, nl=True):
    log(text, symbol, fg=fg, bg=bg, bold=bold, nl=nl)


def log_success(text, *, symbol='+', fg='green', bg=None, bold=True, nl=True):
    log(text, symbol, fg=fg, bg=bg, bold=bold, nl=nl)


def log_warn(text, *, symbol='!', fg='magenta', bg=None, bold=True, nl=True):
    log(text, symbol, fg=fg, bg=bg, bold=bold, nl=nl)


def log_error(text, *, symbol='!', fg='red', bg=None, bold=True, nl=True):
    log(text, symbol, fg=fg, bg=bg, bold=bold, nl=nl)


def print_data(data):
    log_info('Data:')
    click.secho('  pattern ij  y_ij', bold=True)
    for pattern, y_ij in sorted(data.items(), key=lambda t: pattern2ij(t[0])):
        i, j = pattern2ij(pattern)
        click.echo(f'    {pattern}  {i}{j}  {y_ij: >3}')


def print_species(species):
    log_info(f'{len(species)} species: {", ".join(species)}')


def print_results(a, data, model, theta, r):
    log_success(f'Result for hybridization model {model} with theta = {theta}, r = {r}:')
    click.secho('  pattern ij  y_ij  a_ij', bold=True)
    for pattern in sorted(a, key=lambda p: pattern2ij(p)):
        a_ij = a[pattern]
        y_ij = data[pattern]
        i, j = pattern2ij(pattern)
        click.echo(f'    {pattern}  {i}{j}  {y_ij: >3}  {a_ij: >6.3f}')


def print_best(i, best, species, fit, ratio, n0, T1, T3, gamma1, gamma3):
    log_info(f'Best #{i} of {best}')
    click.echo(click.style(' -   perm:', bold=True) + f' {", ".join(species)}')
    click.echo(click.style(' -    fit:', bold=True) + f' {fit:.3f}')
    click.echo(click.style(' -  ratio:', bold=True) + f' {ratio:.3f}')
    click.echo(click.style(' -     n0:', bold=True) + f' {n0:.3f}')
    click.echo(click.style(' -     T1:', bold=True) + f' {T1:.4f}')
    click.echo(click.style(' -     T3:', bold=True) + f' {T3:.4f}')
    click.echo(click.style(' - gamma1:', bold=True) + f' {gamma1:.4f}')
    click.echo(click.style(' - gamma3:', bold=True) + f' {gamma3:.4f}')


def print_rock(a, data, model, permutation, theta, r):
    log_info('For those about to rock:')
    click.secho('  pattern ij  y_ij  a_ij', bold=True)
    for pattern, y_ij in sorted(data.items(), key=lambda t: pattern2ij(fix(t[0], permutation))):
        pattern = fix(pattern, permutation)
        a_ij = a[pattern]
        i, j = pattern2ij(pattern)
        click.echo(f'    {pattern}  {i}{j}  {y_ij: >3}  {a_ij: >6.3f}')
