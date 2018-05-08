__all__ = ('parse_input', 'parse_models', 'parse_best')

import re
import click

from .printers import log_info
from .utils import pattern2ij
from .models import *

regex_separator = re.compile(r'[,;]')


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
        # value = ('2H1', '2H2')
        return tuple()
    model_names = tuple(m for s in value for m in regex_separator.split(s))
    if 'all' in map(lambda s: s.lower(), model_names):
        return all_models
    elif 'H1' in model_names:
        model_names += tuple(m.name for m in models_H1)
    elif 'H2' in model_names:
        model_names += tuple(m.name for m in models_H2)
    # seen = set()
    seen = {'H1', 'H2'}
    seen_add = seen.add
    unique_names = tuple(m for m in model_names if not (m in seen or seen_add(m)))
    for m in unique_names:
        if m not in models_mapping:
            raise click.BadParameter('unknown model name "{}"'.format(m))
    return tuple(models_mapping[m] for m in unique_names)


def parse_best(ctx, param, value):
    if value == 'all':
        return 24
    try:
        return int(value)
    except ValueError:
        raise click.BadParameter('best need to be a number or "all"')
