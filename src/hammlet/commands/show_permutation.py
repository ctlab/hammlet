import click

from ..parsers import parse_input, parse_permutation
from ..printers import log_info, log_success
from ..utils import autotimeit, morph10


@click.command()
@click.option(
    "--preset",
    metavar="<preset>",
    help="Preset data (laur/12-200/12-200-70-50/5-10/29-8...)",
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
    "-p",
    "--permutation",
    metavar="<int...>",
    callback=parse_permutation,
    help="Comma-separated permutation of (1,2,3,4) to use for calculations",
)
@click.option(
    "--output-y",
    "output_filename_y",
    type=click.Path(writable=True),
    metavar="<path>",
    help="Output file with resulting y values",
)
@click.option("--debug", is_flag=True, hidden=True, help="Debug")
@autotimeit
def show_permutation(preset, y, permutation, output_filename_y, debug):
    """Show permutation."""

    _, y = parse_input(preset, None, None, y, verbose=True)
    del preset

    log_info("y: {}".format(" ".join(map(str, y))))
    log_info("Permutation: ({})".format(",".join(map(str, permutation))))

    perm = tuple(p - 1 for p in permutation)
    y_ = morph10(y, perm)
    log_success("Permuted y: {}".format(" ".join(map(str, y_))))

    if output_filename_y:
        log_info("Writing y values to <{}>...".format(output_filename_y))
        with click.open_file(output_filename_y, "w", atomic=True) as f:
            f.write("{}\n".format(" ".join(map(str, y_))))
