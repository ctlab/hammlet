import csv
import sys
from collections import defaultdict

import click
from tabulate import tabulate

from ..optimizer import Optimizer
from ..parsers import presets_db, parse_input
from ..printers import log_debug, log_info, log_success, log_warn
from ..models import models_mapping_mnemonic
from ..utils import autotimeit, pformatf, get_chain, get_pvalue

_levels_data_default = {
    # fmt: off
    4: {
        "H1:TTgg": [(1, 2, 3, 4), (1, 2, 4, 3), (1, 3, 2, 4), (1, 3, 4, 2), (1, 4, 2, 3), (1, 4, 3, 2), (2, 1, 3, 4), (2, 1, 4, 3), (2, 3, 1, 4), (2, 3, 4, 1), (2, 4, 1, 3), (2, 4, 3, 1), (3, 1, 2, 4), (3, 1, 4, 2), (3, 2, 1, 4), (3, 2, 4, 1), (3, 4, 1, 2), (3, 4, 2, 1), (4, 1, 2, 3), (4, 1, 3, 2), (4, 2, 1, 3), (4, 2, 3, 1), (4, 3, 1, 2), (4, 3, 2, 1)],
        "H2:TTgg": [(1, 2, 3, 4), (1, 2, 4, 3), (1, 3, 2, 4), (1, 3, 4, 2), (1, 4, 2, 3), (1, 4, 3, 2), (2, 3, 1, 4), (2, 3, 4, 1), (2, 4, 1, 3), (2, 4, 3, 1), (3, 4, 1, 2), (3, 4, 2, 1)],
    },
    3: {
        "H1:TTg0": [(1, 2, 3, 4), (1, 2, 4, 3), (1, 3, 2, 4), (2, 1, 3, 4), (2, 1, 4, 3), (2, 3, 1, 4), (3, 1, 2, 4), (3, 1, 4, 2), (3, 2, 1, 4), (4, 1, 2, 3), (4, 1, 3, 2), (4, 2, 1, 3)],
        "H1:TT1g": [(1, 2, 3, 4), (1, 2, 4, 3), (1, 3, 2, 4), (1, 3, 4, 2), (1, 4, 2, 3), (1, 4, 3, 2), (2, 1, 3, 4), (2, 1, 4, 3), (2, 3, 1, 4), (2, 3, 4, 1), (2, 4, 1, 3), (2, 4, 3, 1), (3, 1, 2, 4), (3, 1, 4, 2), (3, 2, 1, 4), (3, 2, 4, 1), (3, 4, 1, 2), (3, 4, 2, 1), (4, 1, 2, 3), (4, 1, 3, 2), (4, 2, 1, 3), (4, 2, 3, 1), (4, 3, 1, 2), (4, 3, 2, 1)],
        "H1:TT0g": [(1, 2, 3, 4), (1, 2, 4, 3), (1, 3, 4, 2), (2, 1, 3, 4), (2, 1, 4, 3), (2, 3, 4, 1), (3, 1, 2, 4), (3, 1, 4, 2), (3, 2, 4, 1), (4, 1, 2, 3), (4, 1, 3, 2), (4, 2, 3, 1)],
        "H1:TTg1": [(1, 2, 3, 4), (1, 3, 2, 4), (1, 4, 2, 3), (2, 3, 1, 4), (2, 4, 1, 3), (3, 4, 1, 2)],
        "H2:T0gg": [(1, 2, 3, 4), (1, 3, 2, 4), (1, 4, 2, 3), (2, 3, 1, 4), (2, 4, 1, 3), (3, 4, 1, 2)],
    },
    2: {
        "H1:0Tng": [(1, 2, 3, 4), (1, 2, 4, 3), (1, 3, 4, 2), (2, 1, 3, 4), (2, 1, 4, 3), (2, 3, 4, 1), (3, 1, 2, 4), (3, 1, 4, 2), (3, 2, 4, 1), (4, 1, 2, 3), (4, 1, 3, 2), (4, 2, 3, 1)],
        "H1:T0g0": [(1, 2, 3, 4), (1, 2, 4, 3), (1, 3, 2, 4), (2, 1, 3, 4), (2, 1, 4, 3), (2, 3, 1, 4), (3, 1, 2, 4), (3, 1, 4, 2), (3, 2, 1, 4), (4, 1, 2, 3), (4, 1, 3, 2), (4, 2, 1, 3)],
        "H1:T0g1": [(1, 2, 3, 4), (1, 3, 2, 4), (1, 4, 2, 3), (2, 3, 1, 4), (2, 4, 1, 3), (3, 4, 1, 2)],
        "H1:TT10": [(1, 2, 3, 4), (1, 2, 4, 3), (1, 3, 2, 4), (2, 1, 3, 4), (2, 1, 4, 3), (3, 1, 4, 2)],
        "H1:TT01": [(1, 2, 3, 4), (1, 3, 2, 4), (1, 4, 2, 3), (2, 1, 3, 4), (2, 3, 1, 4), (2, 4, 1, 3), (3, 1, 2, 4), (3, 2, 1, 4), (3, 4, 1, 2), (4, 1, 2, 3), (4, 2, 1, 3), (4, 3, 1, 2)],
    },
    1: {
        "H1:0Tn1": [(1, 2, 3, 4), (1, 3, 2, 4), (1, 4, 2, 3), (2, 3, 1, 4), (2, 4, 1, 3), (3, 4, 1, 2)],
        "H1:T010": [(1, 2, 3, 4), (1, 2, 4, 3), (1, 3, 2, 4)],
        "H1:T00n": [(1, 2, 3, 4), (2, 1, 3, 4), (3, 1, 2, 4), (4, 1, 2, 3)],
    },
    0: {
        "H1:00nn": [(1, 2, 3, 4)]
    },
    # fmt: on
}
_levels_data_default = {
    level: {
        models_mapping_mnemonic[mnemo]: perms for mnemo, perms in level_data.items()
    }
    for level, level_data in _levels_data_default.items()
}


@click.command()
@click.option(
    "-l",
    "--levels",
    "levels_filename",
    metavar="<path|->",
    type=click.Path(exists=True, allow_dash=True),
    help="File with levels data",
)
@click.option(
    "--preset",
    type=click.Choice(presets_db),
    metavar="<preset>",
    help="Data preset ({})".format("/".join(presets_db.keys())),
)
@click.option(
    "-y",
    nargs=10,
    type=int,
    metavar="<int...>",
    help="Space-separated list of "
    + click.style("ten", bold=True)
    + " y values (y11 y12 y13 y14 y22 y23 y24 y33 y34 y44)",
)
@click.option(
    "-r",
    nargs=4,
    type=float,
    metavar="<float...>",
    default=(1, 1, 1, 1),
    show_default=True,
    help="Space-separated list of " + click.style("four", bold=True) + " r values",
)
@click.option(
    "--output-mle",
    "output_filename_mle",
    type=click.Path(writable=True),
    metavar="<path>",
    help="Output file with MLE results table",
)
@click.option(
    "--output-chain",
    "output_filename_chain",
    type=click.Path(writable=True),
    metavar="<path>",
    help="Output file with a resulting chain",
)
@click.option(
    "--output-result",
    "output_filename_result",
    type=click.Path(writable=True),
    metavar="<path>",
    help="Output file with a result",
)
@click.option(
    "-p",
    "--pvalue",
    "critical_pvalue",
    type=float,
    metavar="<float>",
    default=0.05,
    show_default=True,
    help="p-value for statistical tests",
)
@click.option(
    "--method",
    type=click.Choice(["SLSQP", "L-BFGS-B", "TNC"]),
    default="SLSQP",
    show_default=True,
    help="Optimization method",
)
@click.option(
    "--theta0",
    nargs=5,
    type=float,
    metavar="<n0 T1 T3 g1 g3>",
    help="Space-separated list of "
    + click.style("five", bold=True)
    + " initial theta components (n0 T1 T3 gamma1 gamma3)",
)
@click.option("--debug", is_flag=True, hidden=True, help="Debug")
@autotimeit
def levels(
    levels_filename,
    preset,
    y,
    r,
    output_filename_mle,
    output_filename_chain,
    output_filename_result,
    critical_pvalue,
    method,
    theta0,
    debug,
):
    """Compute levels."""

    y = parse_input(preset, y, verbose=True)
    del preset
    log_info("y: {}".format(" ".join(map(str, y))))
    log_info("r: ({})".format(", ".join(map(pformatf, r))))

    if not theta0:
        theta0 = (round(0.6 * sum(y), 5), 0.5, 0.5, 0.5, 0.5)
        if debug:
            log_debug("Using default theta0: {}".format(theta0))

    def parse_perm(perm):
        if perm.startswith("{") or perm.startswith("("):
            perm = perm[1:]
        if perm.endswith("}") or perm.endswith(")"):
            perm = perm[:-1]
        return tuple(map(int, perm.split(",")))

    if levels_filename:
        log_info("Reading levels data from <{}>...".format(levels_filename))
        levels_data = {
            level: defaultdict(list) for level in range(5)
        }  # {level: {model: [perm]}
        if sys.version > "3":
            levels_file = open(levels_filename, newline="")
        else:
            levels_file = open(levels_filename, "rb")
        with levels_file as f:
            reader = csv.DictReader(f)
            for row in reader:
                level = int(row["Level"])
                assert 0 <= level <= 4
                model = models_mapping_mnemonic[
                    "{}:{}".format(row["Branch"], row["Case"])
                ]
                if model.name != row["Type"]:
                    log_warn(
                        "Model name mismatch: model.name={}, Type={}".format(
                            model.name, row["Type"]
                        )
                    )
                perm = parse_perm(row["Permut"])
                levels_data[level][model].append(perm)
        del reader, row, level, model, perm, levels_file
    else:
        log_info("Using default levels data")
        levels_data = _levels_data_default

    # ================
    from ..models import all_models

    models_in_data = set()
    for level_data in levels_data.values():
        for model in level_data:
            models_in_data.add(model)
    missed_models = set(all_models) - models_in_data
    if missed_models:
        log_warn("Missed models: {}".format(" ".join(map(str, missed_models))))
    del all_models, missed_models, models_in_data, level_data, model
    # ================

    optimizer = Optimizer(y, r, theta0, method, debug=debug)
    results_level = {level: [] for level in levels_data}

    log_info("Optimizing...")
    for level, level_data in levels_data.items():
        for model, perms in level_data.items():
            results = optimizer.many_perms(model, perms, sort=False)
            results_level[level].extend(results)
        results_level[level].sort(key=lambda t: t.LL, reverse=True)
    del level, level_data, model, perms, results

    data = []
    for level in reversed(range(5)):
        for result in results_level[level]:
            model = result.model
            perm = result.permutation
            LL = result.LL
            n0, T1, T3, gamma1, gamma3 = result.theta
            data.append(
                (
                    level,
                    model.name,
                    model.mnemonic_name,
                    ",".join(map(str, perm)),
                    LL,
                    n0,
                    T1,
                    T3,
                    gamma1,
                    gamma3,
                )
            )
            # ========
            if abs(LL - results_level[level][0].LL) < 1e-3:
                data[-1] = tuple(click.style(str(x), fg="yellow") for x in data[-1])
            # ========
            del result, model, perm, LL, n0, T1, T3, gamma1, gamma3
        del level
    headers = ["Lvl", "Model", "Mnemo", "Perm", "LL", "n0", "T1", "T3", "g1", "g3"]
    if output_filename_mle:
        log_info("Writing MLE results to <{}>...".format(output_filename_mle))
        with click.open_file(output_filename_mle, "w", atomic=True) as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(headers)
            for row in data:
                writer.writerow(map(click.unstyle, map(str, row)))
    table = tabulate(
        data,
        headers=[click.style(s, bold=True) for s in headers],
        numalign="center",
        stralign="center",
        floatfmt=".3f",
        tablefmt="simple",
    )
    log_success("MLE results:")
    click.echo(table)
    del data, headers, table

    # was: max(results, key=lambda t: t.LL)
    # results are already sorted, so we can just pull the first one
    best_results_level = {level: results[0] for level, results in results_level.items()}

    data = []
    for level in reversed(range(5)):
        result = best_results_level[level]
        model = result.model
        perm = result.permutation
        LL = result.LL
        n0, T1, T3, gamma1, gamma3 = result.theta
        if level == 4:
            p = None
        else:
            _, p = get_pvalue(best_results_level[level + 1], result)
        data.append(
            [
                level,
                model.name,
                model.mnemonic_name,
                ",".join(map(str, perm)),
                LL,
                n0,
                T1,
                T3,
                gamma1,
                gamma3,
                p,
            ]
        )
        del result, model, perm, LL, n0, T1, T3, gamma1, gamma3, p
    headers = [
        "Lvl",
        "Model",
        "Mnemo",
        "Perm",
        "LL",
        "n0",
        "T1",
        "T3",
        "g1",
        "g3",
        "pvalue",
    ]
    table = tabulate(
        data,
        headers=[click.style(s, bold=True) for s in headers],
        numalign="center",
        stralign="center",
        # floatfmt=".3f",
        floatfmt=[
            None,
            None,
            None,
            None,
            ".2f",
            ".3f",
            ".3f",
            ".3f",
            ".3f",
            ".3f",
            ".5f",
        ],
        tablefmt="simple",
        missingval="-",
    )
    log_success("Best result on each level:")
    click.echo(table)
    del data, headers, table

    log_info("Calculating chain...")
    path = [best_results_level[level].model.name for level in reversed(range(5))]
    results = {result.model.name: result for result in best_results_level.values()}
    chain = get_chain(path, results, critical_pvalue)
    if output_filename_chain:
        log_info("Writing chain to <{}>...".format(output_filename_chain))
        with click.open_file(output_filename_chain, "w", atomic=True) as f:
            f.write(
                "{}\n".format(
                    " -> ".join(
                        "{}[{:.3f}]".format(model, results[model].LL) for model in chain
                    )
                )
            )
    log_success("Chain over levels:")
    click.echo(
        "    "
        + " -> ".join("{}[{:.2f}]".format(model, results[model].LL) for model in chain)
    )

    simple_model = chain[-1]
    if output_filename_result:
        log_info("Writing result to <{}>...".format(output_filename_result))
        with click.open_file(output_filename_result, "w", atomic=True) as f:
            writer = csv.writer(f, lineterminator="\n")
            headers = "Model Mnemo Permutation n0 T1 T3 g1 g3 Prev.Model Prev.pvalue Next.Model Next.pvalue".split()
            simple_level = 5 - len(chain)
            simple_result = results[simple_model]
            assert simple_result.model.name == simple_model
            n0, T1, T3, g1, g3 = simple_result.theta
            if simple_level == 4:
                prev_model = None
                prev_pvalue = None
            else:
                prev_result = best_results_level[simple_level + 1]
                prev_model = prev_result.model.name
                _, prev_pvalue = get_pvalue(prev_result, simple_result)
                del prev_result
            if simple_level == 0:
                next_model = None
            else:
                next_result = best_results_level[simple_level - 1]
                next_model = next_result.model.name
                _, next_pvalue = get_pvalue(simple_result, next_result)
                del next_result
            writer.writerow(headers)
            writer.writerow(
                [
                    simple_model,
                    simple_result.model.mnemonic_name,
                    "{{{}}}".format(",".join(map(str, simple_result.permutation))),
                    n0,
                    T1,
                    T3,
                    g1,
                    g3,
                    prev_model,
                    prev_pvalue,
                    next_model,
                    next_pvalue,
                ]
            )
        del f, writer, headers, simple_level, simple_result, n0, T1, T3, g1, g3
        del prev_model, prev_pvalue, next_model, next_pvalue
    log_success("Insignificantly worse simple model: {}".format(simple_model))
