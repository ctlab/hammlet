import click


def info(text, symbol='*', fg='green', nl=True, bold=True):
    click.secho(f'[{symbol}] {text}', fg=fg, nl=nl, bold=bold)


def print_data(data):
    from .utils import pattern2ij
    info('Data:', symbol=':')
    click.secho('  pattern ij  y_ij', bold=True)
    for pattern, y_ij in sorted(data.items(), key=lambda t: pattern2ij(t[0])):
        i, j = pattern2ij(pattern)
        click.echo(f'    {pattern}  {i}{j}  {y_ij: >3}')


def print_results(a, data, model, theta, r):
    from .utils import pattern2ij
    info(f'Result for hybridization model {model} with theta = {theta}, r = {r}:', symbol='+')
    click.secho('  pattern ij  y_ij  a_ij', bold=True)
    for pattern in sorted(a, key=lambda p: pattern2ij(p)):
        a_ij = a[pattern]
        y_ij = data[pattern]
        i, j = pattern2ij(pattern)
        click.echo(f'    {pattern}  {i}{j}  {y_ij: >3}  {a_ij: >6.3f}')


def print_best(i, best, species, fit, ratio, n0, T1, T3, gamma1, gamma3):
    info(f'Best #{i} of {best}', fg='green', bold=True)
    click.echo(click.style(' -   perm:', bold=True) + f' {", ".join(species)}')
    click.echo(click.style(' -    fit:', bold=True) + f' {fit:.3f}')
    click.echo(click.style(' -  ratio:', bold=True) + f' {ratio:.3f}')
    click.echo(click.style(' -     n0:', bold=True) + f' {n0:.3f}')
    click.echo(click.style(' -     T1:', bold=True) + f' {T1:.4f}')
    click.echo(click.style(' -     T3:', bold=True) + f' {T3:.4f}')
    click.echo(click.style(' - gamma1:', bold=True) + f' {gamma1:.4f}')
    click.echo(click.style(' - gamma3:', bold=True) + f' {gamma3:.4f}')


def print_rock(a, data, model, permutation, theta, r):
    from .utils import fix, pattern2ij
    info('For those about to rock:')
    click.secho('  pattern ij  y_ij  a_ij', bold=True)
    for pattern, y_ij in sorted(data.items(), key=lambda t: pattern2ij(fix(t[0], permutation))):
        pattern = fix(pattern, permutation)
        a_ij = a[pattern]
        i, j = pattern2ij(pattern)
        click.echo(f'    {pattern}  {i}{j}  {y_ij: >3}  {a_ij: >6.3f}')
