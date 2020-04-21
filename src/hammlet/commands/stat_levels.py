import csv

import click
from tabulate import tabulate

from ..models import models_nrds
from ..optimizer import Optimizer
from ..parsers import parse_input, presets_db
from ..printers import log_debug, log_info, log_success
from ..utils import (
    autotimeit,
    get_pvalue,
    grouped_results_to_data,
    pformatf,
    results_to_data,
)


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
    "--output-mle",
    "output_filename_mle",
    type=click.Path(writable=True),
    metavar="<path>",
    help="Output file with MLE results table",
)
@click.option(
    "--output-result",
    "output_filename_result",
    type=click.Path(writable=True),
    metavar="<path>",
    help="Output file with result",
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
    + " initial theta components",
)
@click.option("--debug", is_flag=True, help="Debug")
@autotimeit
def stat_levels(
    preset,
    y,
    r,
    output_filename_mle,
    output_filename_result,
    critical_pvalue,
    method,
    theta0,
    debug,
):
    """Perform 'levels' statistics calculation."""

    y = parse_input(preset, y, verbose=True)
    del preset
    log_info("y: {}".format(" ".join(map(str, y))))
    log_info("r: ({})".format(", ".join(map(pformatf, r))))

    if not theta0:
        theta0 = (round(0.6 * sum(y), 5), 0.5, 0.5, 0.5, 0.5)
        if debug:
            log_debug("Using default theta0: {}".format(theta0))

    levels = ["N4", "N3", "N2", "N1", "N0"]
    optimizer = Optimizer(y, r, theta0, method, debug=debug)

    log_info("Optimizing...")
    results_by_level = {level: optimizer.many(models_nrds[level]) for level in levels}
    best_result_by_level = {
        level: max(results, key=lambda r: r.LL)
        for level, results in results_by_level.items()
    }

    if output_filename_mle:
        headers, data = grouped_results_to_data(results_by_level, group_header="Level")
        log_info("Writing MLE results to <{}>...".format(output_filename_mle))
        with click.open_file(output_filename_mle, "w", atomic=True) as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(headers)
            for row in data:
                writer.writerow(map(str, row))
            del writer
        del headers, data

    headers, data = grouped_results_to_data(
        {level: [best_result] for level, best_result in best_result_by_level.items()},
        group_header="Level",
    )
    table = tabulate(
        data,
        headers=[click.style(s, bold=True) for s in headers],
        numalign="center",
        stralign="center",
        floatfmt=".3f",
        tablefmt="simple",
    )
    del headers, data
    log_success("MLE results (best per level):")
    click.echo(table)

    for level_current, level_next in zip(levels, levels[1:]):
        result_current = best_result_by_level[level_current]
        result_next = best_result_by_level[level_next]
        stat, p = get_pvalue(result_current, result_next, df=1)
        log_info(
            "{}-{}: stat = {:.3f}, p-value = {:.5f}".format(
                level_current, level_next, stat, p
            )
        )
        if p < critical_pvalue:
            log_success("Last p-value < critical_pvalue, stopping")
            break

    log_success(
        "Final result: level {}, model {}".format(level_current, result_current.model)
    )

    if output_filename_result:
        log_info("Writing result to <{}>...".format(output_filename_result))
        with click.open_file(output_filename_result, "w", atomic=True) as f:
            level = level_current
            name = result_current.model.name
            mnemo = result_current.model.mnemonic_name
            LL = result_current.LL
            (n0, T1, T3, g1, g3) = result_current.theta
            if level == levels[0]:
                pbad = 0
            else:
                _, pbad = get_pvalue(
                    best_result_by_level[levels[levels.index(level) - 1]],
                    result_current,
                    df=1,
                )
            if level == levels[-1]:
                pgood = 0
            else:
                _, pgood = get_pvalue(
                    result_current,
                    best_result_by_level[levels[levels.index(level) + 1]],
                    df=1,
                )
            _, ppoly = get_pvalue(result_current, best_result_by_level["N0"], df=1)
            # Ex: [levels],N3,1H3,H1:TT0g,444.45,98.99,1.0,2.0,0,0.5,0.01,0.6,0.0001
            f.write(
                "[levels],{},{},{},{},{},{},{},{},{},{},{},{}\n".format(
                    level, name, mnemo, LL, n0, T1, T3, g1, g3, pbad, pgood, ppoly
                )
            )
