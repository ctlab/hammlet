import re

import click

from .models import all_models, models_H1, models_H2, models_mapping
from .printers import log_info, log_warn
from .utils import pattern2ij

__all__ = ['parse_input', 'parse_models', 'parse_best']


def parse_input(preset, filename, names, y, verbose=False, is_only_a=False):
    if preset:
        if preset == 'laur':
            species = 'Dog Cow Horse Bat'.split()
            ys = tuple(map(int, '22 21 7 11 14 12 18 16 17 24'.split()))
        elif preset == '12-200':
            species = 'A B C D'.split()
            ys = tuple(map(int, '12 12 200 12 12 12 12 12 12 12'.split()))
        elif preset == '12-200-70-50':
            species = 'A B C D'.split()
            ys = tuple(map(int, '12 200 12 70 12 12 12 50 12 12'.split()))
        elif preset == '5-10':
            species = 'A B C D'.split()
            ys = tuple(map(int, '5 10 59 3 5 20 68 125 72 10'.split()))
        else:
            raise click.BadParameter('"{}" is not supported'.format(preset), param_hint='preset')

        if verbose:
            log_info('Using preset "{}"'.format(preset))
    elif filename:
        if verbose:
            log_info('Reading data from <{}>...'.format(filename))
        with click.open_file(filename) as f:
            lines = f.read().strip().split('\n')
            assert len(lines) >= 11, "File must contain a header with names and 10 rows of data (patterns and y values)"

        species = lines[0].strip().split()[:4]
        data = []
        for line in lines[1:]:
            tmp = line.strip().split()
            pattern = ''.join(tmp[:-1])
            assert set(pattern) == set('+-'), "Weird symbols in pattern"
            data.append((pattern2ij(pattern), int(tmp[-1])))
        ys = tuple(y_ij for _, y_ij in sorted(data))
    else:
        if not y:
            if is_only_a:
                if verbose:
                    log_warn('Using ad-hoc default y values!')
                y = tuple(16 for _ in range(10))
            else:
                raise click.BadParameter('missing y values', param_hint='y')
        if not names:
            # Default names
            names = 'A B C D'.split()
        species = names
        ys = tuple(map(int, y))

    return tuple(species), tuple(ys)


def parse_models(ctx, param, value):
    if len(value) == 0:
        # Default value
        # value = ('2H1', '2H2')
        return tuple()
    model_names = tuple(m for s in value for m in re.split(r'[,;]', s))
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
            raise click.BadParameter('unknown model name "{}"'.format(m), param_hint='models')
    return tuple(models_mapping[m] for m in unique_names)


def parse_best(ctx, param, value):
    if value == 'all':
        return len(all_models)
    try:
        return int(value)
    except ValueError:
        raise click.BadParameter('best need to be a number or "all"')
