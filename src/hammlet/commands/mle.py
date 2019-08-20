import csv
import itertools

import click
from tabulate import tabulate

from ..optimizer import Optimizer
from ..parsers import (
    presets_db,
    parse_best,
    parse_input,
    parse_models,
    parse_permutation,
)
from ..printers import log_debug, log_info, log_success
from ..utils import autotimeit, pformatf


@click.command()
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
    "-m",
    "--model",
    "models",
    multiple=True,
    metavar="<name...|all>",
    required=True,
    callback=parse_models,
    help="Comma-separated list of models",
)
@click.option(
    "--output-mle",
    "output_filename_mle",
    type=click.Path(writable=True),
    metavar="<path>",
    help="Output file with MLE results table",
)
@click.option(
    "--best",
    "number_of_best",
    metavar="<int|all>",
    callback=parse_best,
    default="all",
    show_default=True,
    help="Number of best models to show",
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
    help="Use only specified permutation of (1,2,3,4) for calculations",
)
@click.option(
    "--no-polytomy", "is_no_polytomy", is_flag=True, help="Do not show polytomy results"
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
@click.option(
    "--bootstrap",
    "bootstrap_times",
    type=int,
    metavar="<int>",
    default=0,
    show_default=False,
    help="Bootstrap best result n times by applying Poisson to input y values",
)
@click.option(
    "--output-bootstrap",
    "output_filename_bootstrap",
    type=click.Path(writable=True),
    metavar="<path>",
    help="Output file with bootstrap results table",
)
@click.option("--debug", is_flag=True, hidden=True, help="Debug")
@autotimeit
def mle(
    preset,
    y,
    r,
    models,
    output_filename_mle,
    number_of_best,
    is_only_first,
    only_permutation,
    is_no_polytomy,
    method,
    theta0,
    bootstrap_times,
    output_filename_bootstrap,
    debug,
):
    """Perform maximum likelihood estimation."""

    y = parse_input(preset, y, verbose=True)
    del preset
    log_info("y: {}".format(" ".join(map(str, y))))
    log_info("r: ({})".format(", ".join(map(pformatf, r))))
    log_info("Models: {}".format(" ".join(model.name for model in models)))
    log_info("Output file: {}".format(output_filename_mle))

    if not theta0:
        theta0 = (round(0.6 * sum(y), 5), 0.5, 0.5, 0.5, 0.5)
        if debug:
            log_debug("Using default theta0: {}".format(theta0))

    if is_only_first:
        perms = [(1, 2, 3, 4)]
    elif only_permutation:
        perms = [only_permutation]
    else:
        perms = list(itertools.permutations((1, 2, 3, 4)))

    optimizer = Optimizer(y, r, theta0, method, debug=debug)

    log_info("Optimizing...")
    results = optimizer.many(models, perms)
    results.sort(key=lambda t: t.LL, reverse=True)

    data = []
    for result in results:
        model = result.model
        perm = result.permutation
        LL = result.LL
        n0, T1, T3, g1, g3 = result.theta
        data.append(
            (
                model.name,
                model.mnemonic_name,
                ",".join(map(str, perm)),
                LL,
                n0,
                T1,
                T3,
                g1,
                g3,
            )
        )
    headers = ["Model", "Mnemo", "Perm", "LL", "n0", "T1", "T3", "g1", "g3"]
    if output_filename_mle:
        log_info("Writing MLE results to <{}>...".format(output_filename_mle))
        with click.open_file(output_filename_mle, "w", atomic=True) as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for row in data:
                writer.writerow(map(str, row))
    if number_of_best != "all":
        data = data[:number_of_best]
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

    if bootstrap_times > 0:
        from numpy.random import poisson

        best_result = results[0]
        best_model = best_result.model
        best_perm = best_result.permutation

        log_info(
            "Bootstraping best result (model: {}, perm: ({})) {} times...".format(
                best_model.name, ",".join(map(str, best_perm)), bootstrap_times
            )
        )
        data = []
        for _ in range(bootstrap_times):
            y_poissoned = tuple(poisson(y))
            optimizer_boot = Optimizer(y_poissoned, r, theta0, method, debug=debug)
            result_boot = optimizer_boot.one(best_model, best_perm)
            LL = result_boot.LL
            n0, T1, T3, g1, g3 = result_boot.theta
            data.append(
                (
                    " ".join(format(x, " >2") for x in y_poissoned),
                    LL,
                    n0,
                    T1,
                    T3,
                    g1,
                    g3,
                )
            )
        headers = ["y", "LL", "n0", "T1", "T3", "g1", "g3"]
        if output_filename_bootstrap:
            log_info(
                "Writing bootstrap results to <{}>...".format(output_filename_bootstrap)
            )
            with click.open_file(output_filename_bootstrap, "w", atomic=True) as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                for row in data:
                    row = list(row)
                    row[0] = " ".join(row[0].split())
                    writer.writerow(map(str, row))
        table = tabulate(
            data,
            headers=[click.style(s, bold=True) for s in headers],
            numalign="center",
            stralign="center",
            floatfmt=".3f",
            tablefmt="simple",
        )
        log_success("Bootstrap results:")
        click.echo(table)
        del data, headers, table
