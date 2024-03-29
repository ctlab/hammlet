import csv

import click
from tabulate import tabulate

from ..optimizer import Optimizer
from ..parsers import (
    parse_best,
    parse_input,
    parse_models,
    parse_permutation,
    presets_db,
)
from ..printers import log_debug, log_info, log_success
from ..utils import autotimeit, pformatf, results_to_data


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
    "-x",
    "--exclude",
    "excluded_models",
    multiple=True,
    metavar="<name...|all>",
    required=False,
    callback=parse_models,
    help="Comma-separated list of models to exclude",
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
    "--only-first-permutation",
    "is_only_first_permutation",
    is_flag=True,
    help="Use only first permutation (1234) for calculations",
)
@click.option(
    "--only-permutation",
    metavar="<[1-4]{4}>",
    callback=parse_permutation,
    help="Use only specified permutation of (1234) for calculations",
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
    + " initial theta components",
)
@click.option("--debug", is_flag=True, help="Debug")
@autotimeit
def mle(
    preset,
    y,
    r,
    models,
    excluded_models,
    output_filename_mle,
    number_of_best,
    is_only_first_permutation,
    only_permutation,
    is_no_polytomy,
    method,
    theta0,
    debug,
):
    """Perform maximum likelihood estimation."""

    if excluded_models:
        log_debug(
            "Excluding models: {}".format(
                " ".join(model.name for model in excluded_models)
            )
        )
        models = list(set(models) - set(excluded_models))
    if not models:
        log_info("No models left, nothing to do")
        return

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

    if is_only_first_permutation:
        perms = [1234]
    elif only_permutation:
        perms = [only_permutation]
    else:
        perms = "all"

    optimizer = Optimizer(y, r, theta0, method, debug=debug)

    log_info("Optimizing...")
    results = optimizer.many(models, perms, sort=True)

    headers, data = results_to_data(results)
    if output_filename_mle:
        log_info("Writing MLE results to <{}>...".format(output_filename_mle))
        with click.open_file(output_filename_mle, "w", atomic=True) as f:
            writer = csv.writer(f, lineterminator="\n")
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
    del headers, data
    log_success("MLE results:")
    click.echo(table)
