import csv

import click
from numpy.random import poisson
from tabulate import tabulate

from ..optimizer import Optimizer
from ..parsers import parse_input, parse_models, parse_permutation, presets_db
from ..printers import log_debug, log_info, log_success
from ..utils import autotimeit, pformatf


@click.command()
@click.option(
    "--preset",
    type=click.Choice(presets_db),
    metavar="<preset>",
    help="Data preset ({})".format("/".join(presets_db.keys())),
    hidden=True,
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
    metavar="<name>",
    required=True,
    callback=parse_models,
    help="Model",
)
@click.option(
    "--permutation",
    metavar="<int...>",
    required=True,
    callback=parse_permutation,
    help="Permutations to use for calculations",
)
@click.option(
    "-n",
    "--times",
    "bootstrap_times",
    type=int,
    metavar="<int>",
    required=True,
    help="Bootstrap N times by applying Poisson to input y values",
)
@click.option(
    "--output-bootstrap",
    "output_filename_bootstrap",
    type=click.Path(writable=True),
    metavar="<path>",
    help="Output file with bootstrap results table",
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
    + " initial theta components",
)
@click.option("--debug", is_flag=True, help="Debug")
@autotimeit
def bootstrap(
    preset,
    y,
    r,
    models,
    permutation,
    bootstrap_times,
    output_filename_bootstrap,
    method,
    theta0,
    debug,
):
    """Perform MLE bootstrap."""

    if len(models) != 1:
        raise click.BadParameter("specify exactly one model", param_hint="-m/--model")

    y = parse_input(preset, y, verbose=True)
    model = models[0]
    del preset, models
    log_info("y: {}".format(" ".join(map(str, y))))
    log_info("r: ({})".format(", ".join(map(pformatf, r))))
    log_info("Model: {}".format(model.name))
    log_info("Permutation: ({})".format(",".join(map(str, permutation))))
    log_info("Output file: {}".format(output_filename_bootstrap))

    if not theta0:
        theta0 = (round(0.6 * sum(y), 5), 0.5, 0.5, 0.5, 0.5)
        if debug:
            log_debug("Using default theta0: {}".format(theta0))

    log_info("Bootstraping {} times...".format(bootstrap_times))
    data = []
    for _ in range(bootstrap_times):
        y_poissoned = tuple(poisson(y))
        optimizer_boot = Optimizer(y_poissoned, r, theta0, method, debug=debug)
        result_boot = optimizer_boot.one(model, permutation)
        LL = result_boot.LL
        n0, T1, T3, g1, g3 = result_boot.theta
        data.append(
            (" ".join(format(x, " >2") for x in y_poissoned), LL, n0, T1, T3, g1, g3)
        )
    headers = ["y", "LL", "n0", "T1", "T3", "g1", "g3"]
    if output_filename_bootstrap:
        log_info(
            "Writing bootstrap results to <{}>...".format(output_filename_bootstrap)
        )
        with click.open_file(output_filename_bootstrap, "w", atomic=True) as f:
            writer = csv.writer(f, lineterminator="\n")
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
