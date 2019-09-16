import csv
import itertools
from collections import OrderedDict

import click
from tabulate import tabulate

from ..optimizer import Optimizer
from ..parsers import presets_db, parse_input, parse_permutation
from ..printers import log_debug, log_info, log_success
from ..models import models_H1, models_H2, models_hierarchy
from ..utils import autotimeit, pformatf, get_paths, get_chains


@click.command()
@click.option(
    "-g", "--group", type=click.Choice(["H1", "H2"]), required=True, help="Model group"
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
    "--output-chains",
    "output_filename_chains",
    type=click.Path(writable=True),
    metavar="<path>",
    help="Output file with resulting chains",
)
@click.option(
    "--only-first",
    "is_only_first",
    is_flag=True,
    help="Use only first permutation (1,2,3,4) for calculations",
)
@click.option(
    "--only-permutation",
    metavar="<int...>",
    callback=parse_permutation,
    help="Comma-separated permutation of (1,2,3,4) to use for calculations",
)
@click.option(
    "--free-permutation",
    "is_free_permutation",
    is_flag=True,
    help="Use best permutation for each simpler model",
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
@click.option("--debug", is_flag=True, help="Debug")
@autotimeit
def chains(
    group,
    preset,
    y,
    r,
    output_filename_mle,
    output_filename_chains,
    is_only_first,
    only_permutation,
    is_free_permutation,
    critical_pvalue,
    method,
    theta0,
    debug,
):
    """Compute insignificantly worse simple models."""

    y = parse_input(preset, y, verbose=True)
    del preset
    log_info("Model group: {}".format(group))
    log_info("Hierarchy: {}".format("free" if is_free_permutation else "non-free"))
    log_info("y: {}".format(" ".join(map(str, y))))
    log_info("r: ({})".format(", ".join(map(pformatf, r))))

    if not theta0:
        theta0 = (round(0.6 * sum(y), 5), 0.5, 0.5, 0.5, 0.5)
        if debug:
            log_debug("Using default theta0: {}".format(theta0))

    if group == "H1":
        models = models_H1
    elif group == "H2":
        models = models_H2
    else:
        raise ValueError("Unsupperted group '{}'".format(group))
    hierarchy = models_hierarchy[group]["free" if is_free_permutation else "non-free"]

    if is_only_first:
        perms = [(1, 2, 3, 4)]
    elif only_permutation:
        perms = [only_permutation]
    else:
        perms = list(itertools.permutations((1, 2, 3, 4)))

    optimizer = Optimizer(y, r, theta0, method, debug=debug)
    results_chain = OrderedDict()

    log_info("Optimizing...")
    if is_free_permutation:
        for model in models:
            results = optimizer.many_perms(model, perms, sort=True)
            best_result = results[0]
            results_chain[model.name] = best_result

        del model, results, best_result
    else:
        model_complex = models[0]
        results_complex = optimizer.many_perms(model_complex, perms, sort=True)
        best_complex_result = results_complex[0]
        results_chain[model_complex.name] = best_complex_result

        results = optimizer.many_models(
            models[1:], best_complex_result.permutation, sort=False
        )
        for result in results:
            results_chain[result.model.name] = result

        del model_complex, results_complex, best_complex_result, result, results

    data = []
    for result in results_chain.values():
        model = result.model
        perm = result.permutation
        LL = result.LL
        n0, T1, T3, gamma1, gamma3 = result.theta
        data.append(
            (
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
    headers = ["Model", "Mnemo", "Perm", "LL", "n0", "T1", "T3", "g1", "g3"]
    if output_filename_mle:
        log_info("Writing MLE results to <{}>...".format(output_filename_mle))
        with click.open_file(output_filename_mle, "w", atomic=True) as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(headers)
            for row in data:
                writer.writerow(map(str, row))
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
    del data, table

    log_info("Calculating chains...")
    paths = get_paths(hierarchy, models[0])
    chains = get_chains(paths, results_chain, critical_pvalue)
    chains = [chain for chain in chains if len(chain) > 1]  # drop 1-length chains
    chains = list(set(map(tuple, chains)))  # drop duplicates

    if output_filename_chains:
        log_info("Writing chains to <{}>...".format(output_filename_chains))
        with click.open_file(output_filename_chains, "w", atomic=True) as f:
            for chain in chains:
                f.write(
                    "{}\n".format(
                        " -> ".join(
                            "{}[{:.3f}]".format(model, results_chain[model].LL)
                            for model in chain
                        )
                    )
                )

    log_success("Chains:")
    for chain in chains:
        click.echo(
            "    "
            + " -> ".join(
                "{}[{:.2f}]".format(model, results_chain[model].LL) for model in chain
            )
        )

    simple_models = set(chain[-1] for chain in chains)
    log_success(
        "Insignificantly worse simple models: {}".format(" ".join(simple_models))
    )
