__all__ = ('parse_input', 'parse_models', 'parse_best')

from collections import OrderedDict

import click

from .printers import log_info
from .utils import all_models, ij2pattern, get_model_func


def parse_input(filename, names, y, verbose=False):
    if filename:
        if verbose:
            log_info('Reading data from <{}>...'.format(filename))
        with click.open_file(filename) as f:
            lines = f.read().strip().split('\n')
            assert len(lines) >= 11, "File must contain header with names and 10 rows of data (patterns and y values)"

        species = lines[0].strip().split()[:4]
        data = OrderedDict()  # {pattern: y_ij}
        for line in lines[1:]:
            tmp = line.strip().split()
            pattern = ''.join(tmp[:-1])
            assert set(pattern) == set('+-'), "Weird symbols in pattern"
            y_ij = int(tmp[-1])
            data[pattern] = y_ij
    else:
        if not y:
            raise click.BadParameter('missing y values')
        species = names
        data = OrderedDict()  # {pattern: y_ij}
        ys = iter(y)
        for i in range(4):
            for j in range(i, 4):
                pattern = ij2pattern(i + 1, j + 1)
                data[pattern] = next(ys)
    return species, data


def parse_models(ctx, param, value):
    if len(value) == 0:
        # Default value
        return ('2H1', '2H2')
    elif 'all' in value:
        return all_models
    else:
        if not all(map(get_model_func, value)):
            raise click.BadParameter('unknown model name (or anything else...)')
        return value


def parse_best(ctx, param, value):
    if value == 'all':
        return 24
    try:
        return int(value)
    except ValueError:
        raise click.BadParameter('best need to be a number or "all"')
