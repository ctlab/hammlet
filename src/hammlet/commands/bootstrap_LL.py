import csv

import click
import numpy as np
from tabulate import tabulate

from ..models import models_nrds
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
    "-l",
    "--level",
    "level_senior",
    metavar="<level>",
    required=True,
    type=click.Choice(["N{}".format(i) for i in range(0, 4 + 1)]),
    help="Level (senior) for bootstrap",
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
# @click.option(
#     "--permutation",
#     metavar="<int...>",
#     required=True,
#     callback=parse_permutation,
#     help="Permutations to use for calculations",
# )
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
    preset,
    y,
    r,
    level_senior,
    models,
    # permutation,
    bootstrap_times,
    output_filename_bootstrap,
    method,
    theta0,
    debug,
):
    """Perform MLE bootstrap-LL."""

    if len(models) != 1:
        raise click.BadParameter(
            "specify exactly one (junior) model", param_hint="-m/--models"
        )

    y = parse_input(preset, y, verbose=True)
    del preset

    model_junior = models[0]
    del models

    models_senior = models_nrds[level_senior]

    # # Determine senior/junior models
    # for i in range(0, 4 + 1):
    #     ms = models_nrds["N{}".format(i)]
    #     if models[0] in ms:
    #         n1, m1 = i, models[0]
    #     if models[1] in ms:
    #         n2, m2 = i, models[1]
    # if n1 == n2:
    #     raise click.BadParameter(
    #         "specify two models from different N-levels", param_hint="-m/--models"
    #     )
    # if n1 > n2:
    #     model_senior, model_junior = m1, m2
    # else:
    #     model_senior, model_junior = m2, m1
    # del models

    log_info("y: {}".format(" ".join(map(str, y))))
    log_info("r: ({})".format(", ".join(map(pformatf, r))))
    log_info("Senior level: {}".format(level_senior))
    log_info("Junior model: {}".format(model_junior.name))
    # log_info("Permutation: ({})".format(",".join(map(str, permutation))))
    log_info("Output file: {}".format(output_filename_bootstrap))

    if not theta0:
        theta0 = (round(0.6 * sum(y), 5), 0.5, 0.5, 0.5, 0.5)
        if debug:
            log_debug("Using default theta0: {}".format(theta0))

    log_info(
        "Bootstraping {}/{} (senior/junior) {} times...".format(
            level_senior, model_junior.name, bootstrap_times
        )
    )
    data = []
    for _ in range(bootstrap_times):
        y_poissoned = tuple(np.random.poisson(y))
        optimizer_boot = Optimizer(y_poissoned, r, theta0, method, debug=debug)

        results_boot_senior = optimizer_boot.many(models_senior, "model")
        results_boot_junior = optimizer_boot.many_perms(model_junior, "model")

        best_result_senior = max(results_boot_senior, key=lambda it: it.LL)
        best_result_junior = max(results_boot_junior, key=lambda it: it.LL)

        LLx = best_result_senior.LL
        LLy = best_result_junior.LL
        LL_diff = LLx - LLy
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
    headers = ["y", "Mx", "permx", "LLx", "My", "permy", "LLy", "LLx-LLy"]
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
