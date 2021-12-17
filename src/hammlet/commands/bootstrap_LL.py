import csv

import click
import numpy as np
from tabulate import tabulate

from ..models import constraint_bounds, constraint_value, models_nrds
from ..optimizer import Optimizer
from ..parsers import parse_models
from ..printers import log_debug, log_info, log_success
from ..utils import autotimeit, get_a, pformatf


@click.command()
@click.option(
    "-l",
    "--level",
    "level_senior",
    metavar="<level>",
    required=True,
    type=click.Choice(["N{}".format(i) for i in range(0, 4 + 1)]),
    help="Level (senior) for bootstrap",
)
@click.option(
    "-x",
    "--exclude",
    "excluded_models",
    multiple=True,
    metavar="<name...|all>",
    required=False,
    callback=parse_models,
    help="Comma-separated list of models to exclude from the senior level",
)
@click.option(
    "-m",
    "--model",
    "models",
    metavar="<name>",
    multiple=True,  # actually, this arg must be single, but the parser only supports list of models
    required=True,
    callback=parse_models,
    help="Model (junior) for bootstrap",
)
@click.option(
    "-t",
    "--theta",
    nargs=5,
    type=float,
    metavar="<n0 T1 T3 g1 g3>",
    required=True,
    help="Space-separated list of "
    + click.style("five", bold=True)
    + " theta components for a_ij calculation",
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
def bootstrap_LL(
    level_senior,
    excluded_models,
    models,
    theta,
    r,
    bootstrap_times,
    output_filename_bootstrap,
    method,
    theta0,
    debug,
):
    """Perform MLE bootstrap-LL."""

    if len(models) != 1:
        raise click.BadParameter(
            "specify exactly one junior model", param_hint="-m/--model"
        )
    model_junior = models[0]
    del models

    bounds = model_junior.get_safe_bounds()
    theta = tuple(constraint_value(param, bound) for param, bound in zip(theta, bounds))
    del bounds

    a = get_a(model=model_junior, theta=theta, r=r)

    log_info("Senior level: {}".format(level_senior))
    log_info("Junior model: {}".format(model_junior.name))
    log_info("theta: (n0={}, T1={}, T3={}, g1={}, g3={})".format(*map(pformatf, theta)))
    log_info("r: ({})".format(", ".join(map(pformatf, r))))
    log_info("a-ij: ({})".format(", ".join(pformatf(aij, 1) for aij in a)))
    log_info("Output file: {}".format(output_filename_bootstrap))

    if not theta0:
        theta0 = (10, 0.5, 0.5, 0.5, 0.5)
        if debug:
            log_debug("Using default theta0: {}".format(theta0))

    if excluded_models:
        log_info(
            "Excluding models: {}".format(
                " ".join(model.name for model in excluded_models)
            )
        )
    models_senior = list(set(models_nrds[level_senior]) - set(excluded_models))
    del excluded_models

    log_info(
        "Senior models: {}".format(" ".join(model.name for model in models_senior))
    )

    if not models_senior:
        raise ValueError("No models left on senior level")

    log_info(
        "Bootstraping {}/{} (senior/junior) {} times...".format(
            level_senior, model_junior.name, bootstrap_times
        )
    )
    data = []
    for _ in range(bootstrap_times):
        y_poissoned = tuple(np.random.poisson(a))
        optimizer_boot = Optimizer(y_poissoned, r, theta0, method, debug=debug)

        results_boot_senior = optimizer_boot.many(models_senior, "model")
        results_boot_junior = optimizer_boot.many_perms(model_junior, "model")

        best_result_senior = max(results_boot_senior, key=lambda it: it.LL)
        best_result_junior = max(results_boot_junior, key=lambda it: it.LL)

        LLx = best_result_senior.LL
        LLy = best_result_junior.LL
        LL_diff = 2 * (LLx - LLy)
        data.append(
            (
                " ".join(format(x, " >2") for x in y_poissoned),
                best_result_senior.model.name,
                "".join(map(str, best_result_senior.permutation)),
                LLx,
                model_junior.name,
                "".join(map(str, best_result_junior.permutation)),
                LLy,
                LL_diff,
            )
        )
    headers = ["y", "Mx", "px", "LLx", "My", "py", "LLy", "LLx-LLy"]
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
