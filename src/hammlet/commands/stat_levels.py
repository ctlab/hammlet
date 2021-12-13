import csv

import click
from tabulate import tabulate

from ..models import models_nrds
from ..optimizer import Optimizer
from ..parsers import parse_ecdfs, parse_input, parse_models, presets_db
from ..printers import log_debug, log_info, log_success, log_warn
from ..utils import (
    autotimeit,
    get_a,
    get_LL2,
    get_pvalue,
    grouped_results_to_data,
    pformatf,
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
    "--ecdfs",
    metavar="<N4-N3, N3-N2, N2-N1, N1-N0>",
    callback=parse_ecdfs,
    help="[ecdf] Comma-separated list of "
    + click.style("four", bold=True)
    + " precomputed critical values for N4-N3,...,N1-N0",
)
@click.option(
    "-n",
    "--times",
    "bootstrap_times",
    type=int,
    metavar="<int>",
    help="[ecdf] Number of bootstrap samples",
)
@click.option(
    "--use-best-senior-model",
    is_flag=True,
    help="[ecdf] Optimize only the best senior model during bootstrap in ecdf",
)
@click.option("--debug", is_flag=True, help="Debug")
@autotimeit
def stat_levels(
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
    ecdfs,
    bootstrap_times,
    use_best_senior_model,
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

    if bootstrap_times and not ecdf:
        raise click.BadParameter(
            "bootstrap is only performed with --ecdf flag", param_hint="-n/--times"
        )

    if use_best_senior_model and not ecdf:
        raise click.BadParameter(
            "option --use-best-senior-model only makes sense with --ecdf flag",
            param_hint="--use-best-senior-model",
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

    levels = ["N4", "N3", "N2", "N1", "N0"]
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
    # Drop empty levels
    levels = [level for level in levels if models_by_level[level]]

    log_info("Optimizing...")
    results_by_level = {
        level: optimizer.many(models_by_level[level], "model") for level in levels
    }
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
        if ecdf:  # and level_next != "N0":
            if ecdfs is not None:
                z = ecdfs[levels.index(level_current)]
            else:
                a = get_a(model=result_next.model, theta=result_next.theta, r=r)
                if use_best_senior_model:
                    models_high = [result_current.model]
                    log_info(
                        "Bootstrapping {}/{} {} times...".format(
                            result_current.model,
                            result_next.model,
                            rep,
                        )
                    )
                else:
                    models_high = models_by_level[level_current]
                    log_info(
                        "Bootstrapping {}/{} {} times...".format(
                            level_current,
                            result_next.model,
                            rep,
                        )
                    )
                boot = [
                    get_LL2(
                        models_high=models_high,
                        model_low=result_next.model,
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
            LLx = result_current.LL
            LLy = result_next.LL
            d = 2 * (LLx - LLy)
            if ecdfs:
                log_info(
                    "{}-{}: 2*delta LL = {:.3f}, critical LL = {:.3f}".format(
                        level_current, level_next, d, z
                    )
                )
                del LLx, LLy
            else:
                log_info(
                    "{}-{}: 2*delta LL = {:.3f}, critical LL = {:.3f} ({}th of {}, range={:.3f}..{:.3f})".format(
                        level_current, level_next, d, z, i, rep, boot[0], boot[-1]
                    )
                )
                del a, boot, i, LLx, LLy
            if d > z:
                log_success("Last 2*delta LL > critical LL, stopping")
                del d, z
                break
        else:
            stat, p = get_pvalue(result_current, result_next, df=1)
            log_info(
                "{}-{}: stat = {:.3f}, p-value = {:.5f}".format(
                    level_current, level_next, stat, p
                )
            )
            del stat
            if p <= critical_pvalue:
                log_success("Last p-value <= critical_pvalue, stopping")
                level_current = level_next
                result_current = result_next
                del p
                break
    else:  # Note: for...else
        if ecdf:
            log_success("All 2*delta LLs <= critical LLs, accepting polytomy")
        else:
            log_success("All p-value > critical_pvalue, accepting polytomy")
        level_current = level_next
        result_current = result_next

    final_level = level_current
    final_result = result_current

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
            if final_level == levels[0]:
                pbad = 0
            else:
                _, pbad = get_pvalue(
                    best_result_by_level[levels[levels.index(final_level) - 1]],
                    final_result,
                    df=1,
                )
            if final_level == levels[-1]:
                pgood = 0
            else:
                _, pgood = get_pvalue(
                    final_result,
                    best_result_by_level[levels[levels.index(final_level) + 1]],
                    df=1,
                )
            if final_level == "N0":
                ppoly = 1
            else:
                _, ppoly = get_pvalue(
                    final_result, best_result_by_level["N0"], df=int(final_level[1:])
                )
            # Ex: [levels],N3,1H3,H1:TT0g,1234,444.45,98.99,1.0,2.0,0,0.5,0.01,0.6,0.0001
            f.write(
                "[levels],{},{},{},{},{},{},{},{},{},{},{},{},{}\n".format(
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
