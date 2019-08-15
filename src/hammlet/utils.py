import time
from collections import deque
from functools import wraps

import numpy as np
from scipy.stats import chi2

__all__ = [
    "autotimeit",
    "pformatf",
    "morph4",
    "morph10",
    "ij2pattern",
    "pattern2ij",
    "get_a",
    "likelihood",
    "get_paths",
    "get_chain",
    "get_chains",
]


def autotimeit(func, msg="All done in {:.1f} s."):
    from .printers import log_br, log

    @wraps(func)
    def wrapped(*args, **kwargs):
        time_start = time.time()
        result = func(*args, **kwargs)
        log_br()
        log(msg.format(time.time() - time_start), symbol=None, fg="yellow")
        return result

    return wrapped


def pformatf(x, digits=3):
    """Pretty format a float.

    >>> pformatf(3.14159, 3)
    '3.142'
    >>> pformatf(3.14159, 0)
    '3'
    >>> pformatf(2.4001, 2)
    '2.4'
    """
    return "{:.{}f}".format(x, digits).rstrip("0").rstrip(".")


def morph4(iterable, permutation):
    """Apply permutation on 4-iterable.

    >>> morph4('ABCD', None)
    'ABCD'
    >>> morph4('ABCD', (0, 1, 2, 3))
    'ABCD'
    >>> morph4('ABCD', (1, 3, 2, 0))
    'BDCA'
    >>> morph4(('A', 'B', 'C', 'D'), (1, 3, 2, 0))
    ('B', 'D', 'C', 'A')
    """
    if permutation is None:
        return iterable
    if isinstance(iterable, str):
        return "".join(iterable[i] for i in permutation)
    elif isinstance(iterable, list):
        return list(iterable[i] for i in permutation)
    elif isinstance(iterable, tuple):
        return tuple(iterable[i] for i in permutation)
    # elif isinstance(iterable, dict):
    #     return {morph(key, permutation): value for key, value in iterable.items()}
    else:
        raise NotImplementedError(
            "iterable type <{}> is not supported".format(type(iterable))
        )


def morph10(iterable, permutation):
    """
    Apply permutation on 10-iterable. (y-values)

    >>> morph10(42, None)
    42
    >>> morph10((1, 2, 3, 4, 5, 6, 7, 8, 9, 10), (2, 4, 3, 1))
    (5, 7, 6, 2, 10, 9, 4, 8, 3, 1)
    """
    if permutation is None:
        return iterable

    A = {}
    it = iter(iterable)
    for i in range(4):
        for j in range(i, 4):
            A[i, j] = A[j, i] = next(it)

    return tuple(
        A[permutation[i] - 1, permutation[j] - 1] for i in range(4) for j in range(i, 4)
    )


def ij2pattern(i, j):
    """Convert (i,j) pair into string pattern.

    >>> ij2pattern(1, 1)
    '-+++'
    >>> ij2pattern(2, 3)
    '+--+'
    >>> ij2pattern(1, 4)
    '-++-'
    >>> ij2pattern(4, 4)
    '+++-'
    """
    return "".join("-" if t + 1 in (i, j) else "+" for t in range(4))


def pattern2ij(pattern):
    """Convert string pattern into (i,j) pair.

    >>> pattern2ij('-+++')
    (1, 1)
    >>> pattern2ij('+--+')
    (2, 3)
    >>> pattern2ij('-++-')
    (1, 4)
    >>> pattern2ij('+++-')
    (4, 4)
    """
    return (pattern.find("-") + 1, pattern.rfind("-") + 1)


def get_a(model, theta, r):
    """Return `a` values from model.

    >>> from hammlet.models import models_mapping
    >>> theta = (100, 1, 2, 0.6, 0.3)
    >>> r = (1,1,1,1)
    >>> [round(x, 3) for x in get_a(models_mapping['2H1'], theta, r)]
    [49.819, 58.596, 177.022, 2.444, 21.024, 1.816, 51.238, 8.548, 3.715, 1.126]
    >>> [round(x, 3) for x in get_a(models_mapping['2H2'], theta, r)]
    [35.737, 1.858, 175.923, 16.526, 21.781, 69.879, 50.482, 11.716, 0.547, 1.113]
    """
    return tuple(a_ij for _, a_ij in sorted(model(theta, r).items()))


def poisson(a, y):
    """Log-poisson.

    >>> poisson(10, 30).round(5)
    59.07755
    >>> poisson([3, 14], [15, 9]).round(5)
    array([13.47918,  9.75152])
    """
    return y * np.log(a) - a


def likelihood(model, y_, theta, r):
    """Log-likelihood.

    L(theta | y) = sum_{i,j} y_ij * ln( a_ij(theta) ) - a_ij(theta)
        where (1 <= i <= j <= 4)

    >>> from hammlet.models import models_mapping
    >>> y = (9,9,100,9,9,9,9,9,9,9)
    >>> theta = (100, 1, 2, .6, .3)
    >>> r = (1,1,1,1)
    >>> likelihood(models_mapping['2H1'], y, theta, r).round(5)
    322.53058
    >>> likelihood(models_mapping['2H2'], y, theta, r).round(5)
    313.37015
    """
    # y_ is morphed
    # Note: do not morph `a`!!!
    a = get_a(model, theta, r)
    return poisson(a, y_).sum()


def get_pvalue(result_complex, result_simple):
    stat = 2 * (result_complex.LL - result_simple.LL)
    p = 1 - chi2.cdf(stat, 1)
    return (stat, p)


def get_paths(hierarchy, initial_model):
    from .models import Model

    if isinstance(initial_model, Model):
        initial_model = initial_model.name

    paths = []  # [model_name]
    q = deque([[initial_model]])

    while q:
        path = q.popleft()
        model_complex = path[-1]
        if model_complex in hierarchy:
            for model_simple in hierarchy[model_complex]:
                q.append(path + [model_simple])
        else:
            paths.append(path)

    return paths


def get_chain(path, results, critical_pvalue):
    # results :: {model_name: result}
    chain = [path[0]]
    for model_complex, model_simple in zip(path, path[1:]):
        result_complex = results[model_complex]
        result_simple = results[model_simple]
        stat, p = get_pvalue(result_complex, result_simple)
        if p >= critical_pvalue:
            chain.append(model_simple)
        else:
            break
    return chain


def get_chains(paths, results, critical_pvalue):
    # results :: {model_name: result}
    return [get_chain(path, results, critical_pvalue) for path in paths]
