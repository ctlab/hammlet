import click
from tabulate import tabulate

__all__ = [
    "log_debug",
    "log_info",
    "log_success",
    "log_warn",
    "log_error",
    "log_br",
    "print_result",
]


def log(text, symbol, fg=None, bg=None, bold=None, nl=True):
    if symbol is None:
        pre = ""
    else:
        pre = "[{: >1}] ".format(symbol)
    click.secho("{}{}".format(pre, text), fg=fg, bg=bg, bold=bold, nl=nl)


def log_debug(text, symbol=".", fg="white", bg=None, bold=None, nl=True):
    log(text, symbol, fg=fg, bg=bg, bold=bold, nl=nl)


def log_info(text, symbol="*", fg="blue", bg=None, bold=True, nl=True):
    log(text, symbol, fg=fg, bg=bg, bold=bold, nl=nl)


def log_success(text, symbol="+", fg="green", bg=None, bold=True, nl=True):
    log(text, symbol, fg=fg, bg=bg, bold=bold, nl=nl)


def log_warn(text, symbol="!", fg="magenta", bg=None, bold=True, nl=True):
    log(text, symbol, fg=fg, bg=bg, bold=bold, nl=nl)


def log_error(text, symbol="!", fg="red", bg=None, bold=True, nl=True):
    log(text, symbol, fg=fg, bg=bg, bold=bold, nl=nl)


def log_br(fg="white", bg=None, bold=False, nl=True):
    log(" ".join("=" * 40), symbol=None, fg=fg, bg=bg, bold=bold, nl=nl)


def print_result(result):
    model = result.model
    perm = result.permutation
    LL = result.LL
    n0, T1, T3, g1, g3 = result.theta
    data = [
        (
            model.name,
            model.mnemonic_name,
            "".join(map(str, perm)),
            LL,
            n0,
            T1,
            T3,
            g1,
            g3,
        )
    ]
    headers = ["Model", "Mnemo", "Perm", "LL", "n0", "T1", "T3", "g1", "g3"]
    table = tabulate(
        data,
        headers=[click.style(s, bold=True) for s in headers],
        numalign="center",
        stralign="center",
        floatfmt=".3f",
        tablefmt="simple",
    )
    click.echo(table)
