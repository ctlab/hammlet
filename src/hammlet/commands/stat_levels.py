import click

from ..models import models_N0, models_N1, models_N2, models_N3, models_N4
from ..optimizer import Optimizer
from ..parsers import parse_input, presets_db
from ..printers import log_debug, log_info, log_success, print_result
from ..utils import autotimeit, get_pvalue, pformatf


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
def stat_levels(preset, y, r, critical_pvalue, method, theta0, debug):
    """Perform 'levels' statistics calculation."""

    y = parse_input(preset, y, verbose=True)
    del preset
    log_info("y: {}".format(" ".join(map(str, y))))
    log_info("r: ({})".format(", ".join(map(pformatf, r))))

    if not theta0:
        theta0 = (round(0.6 * sum(y), 5), 0.5, 0.5, 0.5, 0.5)
        if debug:
            log_debug("Using default theta0: {}".format(theta0))

    optimizer = Optimizer(y, r, theta0, method, debug=debug)

    click.echo()
    log_info("Optimizing N4...")
    results_N4 = optimizer.many(models_N4, sort=True)
    best_result_N4 = max(results_N4, key=lambda r: r.LL)
    log_success("Best result for N4:")
    print_result(best_result_N4)

    #

    click.echo()
    log_info("Optimizing N3...")
    results_N3 = optimizer.many(models_N3, sort=True)
    best_result_N3 = max(results_N3, key=lambda r: r.LL)
    log_success("Best result for N3:")
    print_result(best_result_N3)

    _, p = get_pvalue(best_result_N4, best_result_N3, df=1)
    log_info("p-value for N4-N3: {:.3f}".format(p))
    if p < critical_pvalue:
        log_info("p < critical_pvalue, N4 is the best")
        log_success("Final result: N4, model {}".format(best_result_N4.model.name))
        return
    else:
        log_info("p >= critical_pvalue, N3 is better than N4")
    del p

    #

    click.echo()
    log_info("Optimizing N2...")
    results_N2 = optimizer.many(models_N2, sort=True)
    best_result_N2 = max(results_N2, key=lambda r: r.LL)
    log_success("Best result for N2:")
    print_result(best_result_N2)

    _, p = get_pvalue(best_result_N3, best_result_N2, df=1)
    log_info("p-value for N3-N2: {:.3f}".format(p))
    if p < critical_pvalue:
        log_info("p < critical_pvalue, N3 is the best")
        log_success("Final result: N3, model {}".format(best_result_N3.model.name))
        return
    else:
        log_info("p >= critical_pvalue, N2 is better than N3")
    del p

    #

    click.echo()
    log_info("Optimizing N1...")
    results_N1 = optimizer.many(models_N1, sort=True)
    best_result_N1 = max(results_N1, key=lambda r: r.LL)
    log_success("Best result for N1:")
    print_result(best_result_N1)

    _, p = get_pvalue(best_result_N2, best_result_N1, df=1)
    log_info("p-value for N2-N1: {:.3f}".format(p))
    if p < critical_pvalue:
        log_info("p < critical_pvalue, N2 is the best")
        log_success("Final result: N2, model {}".format(best_result_N2.model.name))
        return
    else:
        log_info("p >= critical_pvalue, N1 is better than N2")
    del p

    #

    click.echo()
    log_info("Optimizing N0...")
    results_N0 = optimizer.many(models_N0, sort=True)
    best_result_N0 = max(results_N0, key=lambda r: r.LL)
    log_success("Best result for N0:")
    print_result(best_result_N0)

    _, p = get_pvalue(best_result_N1, best_result_N0, df=1)
    log_info("p-value for N1-N0: {:.3f}".format(p))
    if p < critical_pvalue:
        log_info("p < critical_pvalue, N1 is the best")
        log_success("Final result: N1, model {}".format(best_result_N1.model.name))
        return
    else:
        log_info("p >= critical_pvalue, N0 is better than N1")
    del p

    log_success("Final result: N0, model {}".format(best_result_N0.model.name))
