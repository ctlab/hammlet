import csv

import click
from tabulate import tabulate

from ..models import models_nrds
from ..optimizer import Optimizer
from ..parsers import parse_input, parse_models, presets_db
from ..printers import log_debug, log_info, log_success
from ..utils import (
    autotimeit,
    get_a,
    get_LL2,
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
@click.option(
    "--ecdf",
    is_flag=True,
    help="Use ecdf criterion",
)
@click.option(
    "-n",
    "--times",
    "bootstrap_times",
    type=int,
    metavar="<int>",
    help="[ecdf] Number of bootstrap samples",
)
@click.option("--debug", is_flag=True, help="Debug")
@autotimeit
def stat_reverse(
    preset,
    y,
    r,
    excluded_models,
    output_filename_mle,
    output_filename_result,
    critical_pvalue,
    method,
    theta0,
    ecdf,
    bootstrap_times,
    debug,
):
    """Perform 'reverse' statistics calculation."""

    y = parse_input(preset, y, verbose=True)
    del preset
    log_info("y: {}".format(" ".join(map(str, y))))
    log_info("r: ({})".format(", ".join(map(pformatf, r))))

    if not theta0:
        theta0 = (round(0.6 * sum(y), 5), 0.5, 0.5, 0.5, 0.5)
        if debug:
            log_debug("Using default theta0: {}".format(theta0))

    if bootstrap_times and not ecdf:
        raise click.BadParameter(
            "bootstrap is only performed with --ecdf flag", param_hint="-n/--times"
        )

    if bootstrap_times:
        rep = bootstrap_times
    else:
        if 0.1 <= critical_pvalue:
            rep = 100
        elif 0.01 <= critical_pvalue < 0.1:
            rep = 1000
        else:
            log_warn("Are you crazy? p={} is too small!".format(critical_pvalue))
            rep = 2000
        # elif 0.001 <= critical_pvalue < 0.01:
        #     rep = 10000
        # elif 0.0001 <= critical_pvalue < 0.001:
        #     rep = 100000
        # else:
        #     rep = 1000000
    log_info("Going to use {} bootstrap samples for p={}".format(rep, critical_pvalue))

    levels = ["N4", "N0", "N1", "N2", "N3"]
    optimizer = Optimizer(y, r, theta0, method, debug=debug)

    if excluded_models:
        log_debug(
            "Excluding models: {}".format(
                " ".join(model.name for model in excluded_models)
            )
        )
    models_by_level = {
        level: list(set(models_nrds[level]) - set(excluded_models)) for level in levels
    }
    del excluded_models
    if not models_by_level["N4"]:
        raise ValueError("No models left in N4")
    # Drop empty levels
    levels = [level for level in levels if models_by_level[level]]

    log_info("Optimizing...")
    results_by_level = {
        level: optimizer.many(models_by_level[level], perms="model") for level in levels
    }
    best_result_by_level = {
        level: max(results, key=lambda r: r.LL)
        for level, results in results_by_level.items()
    }

    if output_filename_mle:
        results_all = [r for rs in results_by_level.values() for r in rs]
        headers, data = results_to_data(results_all)
        del results_all
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

    level_complex = levels[0]
    result_complex = best_result_by_level[level_complex]

    final_level = level_complex
    final_result = result_complex

    for level_simple in levels[1:]:
        result_simple = best_result_by_level[level_simple]
        if ecdf:
            a = get_a(model=result_simple.model, theta=result_simple.theta, r=r)
            boot = [
                get_LL2(
                    model_high=result_complex.model,
                    model_low=result_simple.model,
                    permutation_high=result_complex.permutation,
                    permutation_low=result_simple.permutation,
                    y=a,
                    r=r,
                    theta0=theta0,
                    method=method,
                    debug=debug,
                )
                for _ in range(rep)
            ]
            boot.sort()
            i = int(rep - critical_pvalue * rep)
            z = boot[min([i, rep - 1])]
            LLx = result_complex.LL
            LLy = result_simple.LL
            d = 2 * (LLx - LLy)
            log_info(
                "{}-{}: delta 2*LL = {:.3f}, critical LL = {:.3f} ({}th of {}, range={:.3f}..{:.3f})".format(
                    level_complex, level_simple, d, z, i, rep, boot[0], boot[-1]
                )
            )
            del a, boot, i, LLx, LLy
            if d < z:
                log_success("Last delta 2*LL < critical LL, stopping")
                del d, z
                break
        else:
            df = int(level_complex[1:]) - int(level_simple[1:])
            stat, p = get_pvalue(result_complex, result_simple, df=df)
            log_info(
                "{}-{}: df = {}, stat = {:.3f}, p-value = {:.5f}".format(
                    level_complex, level_simple, df, stat, p
                )
            )
            if p >= critical_pvalue:
                log_success("Last p-value >= critical_pvalue, stopping")
                final_level = level_simple
                final_result = result_simple
                break

    log_success(
        "Final result: level {}, model {}".format(final_level, final_result.model)
    )

    if output_filename_result:
        log_info("Writing result to <{}>...".format(output_filename_result))
        with click.open_file(output_filename_result, "w", atomic=True) as f:
            name = final_result.model.name
            mnemo = final_result.model.mnemonic_name
            permutation = final_result.permutation
            LL = final_result.LL
            (n0, T1, T3, g1, g3) = final_result.theta
            if final_level == levels[0] or final_level == levels[1]:
                pbad = 0
            else:
                level_prev = levels[levels.index(final_level) - 1]
                _, pbad = get_pvalue(
                    result_complex,
                    best_result_by_level[level_prev],
                    df=int(level_complex[1:]) - int(level_prev[1:]),
                )
            pgood = p
            if final_level == "N0":
                ppoly = 1
            else:
                _, ppoly = get_pvalue(
                    final_result, best_result_by_level["N0"], df=int(final_level[1:])
                )
            f.write(
                "[reverse],{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(
                    final_level,
                    name,
                    mnemo,
                    "".join(map(str, permutation)),
                    LL,
                    n0,
                    T1,
                    T3,
                    g1,
                    g3,
                    pbad,
                    pgood,
                    ppoly,
                )
            )
