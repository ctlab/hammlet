import re

import click

from .models import (
    all_models,
    models_H1,
    models_H2,
    models_mapping,
    models_mapping_mnemonic,
    models_nrds,
)
from .printers import log_info, log_warn

__all__ = [
    "presets_db",
    "parse_input",
    "parse_models",
    "parse_best",
    "parse_permutation",
]

presets_db = {  # {preset: y}
    "laur": "22 21 7 11 14 12 18 16 17 24",
    "hctm": "10 8 7 4 21 7 2 39 30 28",
    "12-200": "12 12 200 12 12 12 12 12 12 12",
    "12-200-70-50": "12 200 12 70 12 12 12 50 12 12",
    "5-10": "5 10 59 3 5 20 68 125 72 10",
    "29-8": "29 8 29 29 23 29 29 2 1 2",
}


def parse_input(preset, y, verbose=False, is_only_a=False):
    if preset:
        if preset not in presets_db:
            raise click.BadParameter(
                '"{}" is not supported'.format(preset), param_hint="preset"
            )
        y = presets_db[preset]
        y = tuple(map(int, y.split()))

        if verbose:
            log_info('Using preset "{}"'.format(preset))
    # elif filename:
    #     if verbose:
    #         log_info('Reading data from <{}>...'.format(filename))
    #     with click.open_file(filename) as f:
    #         lines = f.read().strip().split('\n')
    #         assert len(lines) >= 11, "File must contain a header with names and 10 rows of data (patterns and y values)"

    #     species = lines[0].strip().split()[:4]
    #     data = []
    #     for line in lines[1:]:
    #         tmp = line.strip().split()
    #         pattern = ''.join(tmp[:-1])
    #         assert set(pattern) == set('+-'), "Weird symbols in pattern"
    #         data.append((pattern2ij(pattern), int(tmp[-1])))
    #     ys = tuple(y_ij for _, y_ij in sorted(data))
    else:
        if not y:
            if is_only_a:
                if verbose:
                    log_warn("Using ad-hoc default y values!")
                y = tuple(16 for _ in range(10))
            else:
                raise click.BadParameter("missing y values", param_hint="y")
        # if not names:
        #     # Default names
        #     names = 'A B C D'.split()
        # species = names
        y = tuple(map(int, y))

    # return tuple(species), tuple(ys)
    return y


def parse_models(ctx, param, value):
    if not value:
        # Default value
        # value = ('2H1', '2H2')
        return tuple()

    def _get_model_names(s):
        if ":" in s:
            assert s.count(":") == 1
            group, mnemos = s.split(":")
            model_names = []
            for mnemo in re.split(r"[,;]", mnemos):
                m = group + ":" + mnemo
                if m not in models_mapping_mnemonic:
                    raise click.BadParameter(
                        'unknown model mnemonic name "{}"'.format(mnemo),
                        param_hint="models",
                    )
                model_names.append(models_mapping_mnemonic[m].name)
            return model_names
        else:
            return re.split(r"[,;]", s)

    model_names = tuple(m for s in value for m in _get_model_names(s))
    if "all" in map(lambda s: s.lower(), model_names):
        return all_models
    if "H1" in model_names:
        model_names += tuple(m.name for m in models_H1)
    if "H2" in model_names:
        model_names += tuple(m.name for m in models_H2)
    if "N0" in model_names:
        model_names += tuple(m.name for m in models_nrds["N0"])
    if "N1" in model_names:
        model_names += tuple(m.name for m in models_nrds["N1"])
    if "N2" in model_names:
        model_names += tuple(m.name for m in models_nrds["N2"])
    if "N3" in model_names:
        model_names += tuple(m.name for m in models_nrds["N3"])
    if "N4" in model_names:
        model_names += tuple(m.name for m in models_nrds["N4"])
    # seen = set()
    seen = {"H1", "H2", "N0", "N1", "N2", "N3", "N4"}
    seen_add = seen.add
    unique_names = tuple(m for m in model_names if not (m in seen or seen_add(m)))
    for m in unique_names:
        if m not in models_mapping:
            raise click.BadParameter(
                'unknown model name "{}", possible values are: {}'.format(
                    m, ",".join(models_mapping.keys())
                ),
                param_hint="models",
            )
    return tuple(models_mapping[m] for m in unique_names)


def parse_best(ctx, param, value):
    if value.lower() == "all":
        return "all"
    try:
        return int(value)
    except ValueError:
        raise click.BadParameter('must be a number or "all"', param_hint="best")


def parse_permutation(ctx, param, value):
    if value:
        perm = tuple(map(int, value))
        if len(perm) != 4 or sorted(perm) != [1, 2, 3, 4]:
            raise click.BadParameter("must be a permutation of (1,2,3,4)")
        return perm

    # if value:
    #     if sorted(value) != [1, 2, 3, 4]:
    #         raise click.BadParameter('must be a permutation of (1,2,3,4)')
    # return value


def parse_ecdfs(ctx, param, value):
    if value:
        ecdfs = re.split(r"[,;]", value)
        ecdfs = [float(x.strip()) for x in ecdfs]
        if len(ecdfs) != 4:
            raise click.BadParameter("must be exactly 4 values")
        return ecdfs
