__all__ = ('parse_input', 'parse_models', 'parse_best')

import click

from .printers import log_info
from .utils import all_models, pattern2ij


def parse_input(filename, names, y, verbose=False):
    if filename:
        if verbose:
            log_info('Reading data from <{}>...'.format(filename))
        with click.open_file(filename) as f:
            lines = f.read().strip().split('\n')
            assert len(lines) >= 11, "File must contain header with names and 10 rows of data (patterns and y values)"

        species = lines[0].strip().split()[:4]
        data = []
        for line in lines[1:]:
            tmp = line.strip().split()
            pattern = ''.join(tmp[:-1])
            assert set(pattern) == set('+-'), "Weird symbols in pattern"
            data.append((pattern2ij(pattern), int(tmp[-1])))
        ys = [y_ij for _, y_ij in sorted(data)]
    else:
        if not y:
            raise click.BadParameter('missing y values')
        species = names
        ys = list(map(int, y))
    return species, ys


def parse_models(ctx, param, value):
    if len(value) == 0:
        # Default value
        # return ('2H1', '2H2')
        return tuple()
    elif 'all' in value:
        return all_models
    else:
        for model in value:
            if model not in all_models:
                raise click.BadParameter('unknown model name: {}'.format(model))
        return value


def parse_best(ctx, param, value):
    if value == 'all':
        return 24
    try:
        return int(value)
    except ValueError:
        raise click.BadParameter('best need to be a number or "all"')
