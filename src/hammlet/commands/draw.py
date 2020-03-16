import click

from ..drawing import get_drawing_string


@click.command()
@click.option(
    "-m", "--model", type=click.Choice(["H1", "H2"]), required=True, help="Model group"
)
@click.option(
    "-o",
    "--output",
    metavar="<path|->",
    type=click.Path(writable=True, allow_dash=True),
    default="-",
    show_default=True,
    help="Output filename (use `-` for stdout)",
)
@click.option(
    "-T1", "T12", type=float, metavar="<float>", required=True, help="T1=T2 parameter"
)
@click.option(
    "-T3", "T34", type=float, metavar="<float>", required=True, help="T3=T4 parameter"
)
@click.option(
    "-g1", "g1", type=float, metavar="<float>", required=True, help="Gamma1 parameter"
)
@click.option(
    "-g3", "g3", type=float, metavar="<float>", required=True, help="Gamma3 parameter"
)
@click.option(
    "-n",
    "--names",
    metavar="<str>",
    default="1,2,3,4",
    show_default=True,
    help="4 comma-separated names of species",
)
@click.option(
    "-a",
    "--width",
    type=float,
    metavar="<float>",
    default=600,
    show_default=True,
    help="Width",
)
@click.option(
    "-b",
    "--height",
    type=float,
    metavar="<float>",
    default=400,
    show_default=True,
    help="Height",
)
@click.option(
    "--threshold-T",
    "threshold_T",
    type=float,
    metavar="<float>",
    default=0.01,
    show_default=True,
    help="Threshold for almost-zero T",
)
@click.option(
    "--threshold-g",
    "threshold_g",
    type=float,
    metavar="<float>",
    default=0.01,
    show_default=True,
    help="Threshold for almost-zero gamma",
)
@click.option(
    "-cb",
    "--color-background",
    metavar="<color>",
    default="transparent",
    show_default=True,
    help="Background color",
)
@click.option(
    "-ct",
    "--color-tree",
    metavar="<color>",
    default="blue",
    show_default=True,
    help="Tree branches color",
)
@click.option(
    "-ch",
    "--color-hybrid",
    metavar="<color>",
    default="red",
    show_default=True,
    help="Hybridization lines color",
)
@click.option(
    "-cr",
    "--color-ruler",
    metavar="<color>",
    default="green",
    show_default=True,
    help="Ruler color",
)
@click.option(
    "--ruler/--no-ruler",
    "is_draw_ruler",
    default=True,
    show_default=True,
    help="Draw a ruler",
)
def draw(
    model,
    output,
    T12,
    T34,
    g1,
    g3,
    names,
    width,
    height,
    threshold_T,
    threshold_g,
    color_background,
    color_tree,
    color_hybrid,
    color_ruler,
    is_draw_ruler,
):
    """Draw hybridization network."""

    if T12 < threshold_T:
        T12 = 0
    if T34 < threshold_T:
        T34 = 0

    s = get_drawing_string(
        model,
        T12,
        T34,
        g1,
        g3,
        names=names.split(","),
        width=width,
        height=height,
        threshold_g=threshold_g,
        color_background=color_background,
        color_tree=color_tree,
        color_hybrid=color_hybrid,
        color_ruler=color_ruler,
        is_draw_ruler=is_draw_ruler,
    )

    with click.open_file(output, "w") as f:
        f.write(s)
