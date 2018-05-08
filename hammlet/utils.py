__all__ = ('morph4', 'morph10', 'ij2pattern', 'pattern2ij', 'get_a', 'likelihood', 'Worker')

import signal
from itertools import starmap

import numpy as np
from scipy.optimize import minimize


def morph4(iterable, permutation):
    if permutation is None:
        return iterable
    if isinstance(iterable, str):
        return ''.join(iterable[i] for i in permutation)
    elif isinstance(iterable, list):
        return list(iterable[i] for i in permutation)
    elif isinstance(iterable, tuple):
        return tuple(iterable[i] for i in permutation)
    # elif isinstance(iterable, dict):
    #     return {morph(key, permutation): value for key, value in iterable.items()}
    else:
        raise NotImplementedError('iterable type <{}> is not supported'.format(type(iterable)))


def morph10(iterable, permutation):
    if permutation is None:
        return iterable
    A = {}
    it = iter(iterable)
    for i in range(4):
        for j in range(i, 4):
            A[i, j] = A[j, i] = next(it)

    return tuple(A[permutation[i], permutation[j]] for i in range(4) for j in range(i, 4))


def ij2pattern(i, j):
    """Convert (i,j) pair into string pattern.

    Examples:
        ij2pattern(1, 1) -> '-+++'
        ij2pattern(2, 3) -> '+--+'
        ij2pattern(1, 4) -> '-++-'
        ij2pattern(4, 4) -> '+++-'
    """
    return ''.join('-' if t + 1 in (i, j) else '+' for t in range(4))


def pattern2ij(pattern):
    """Convert string pattern into (i,j) pair.

    Examples:
        pattern2ij('-+++') -> (1, 1)
        pattern2ij('+--+') -> (2, 3)
        pattern2ij('-++-') -> (1, 4)
        pattern2ij('+++-') -> (4, 4)
    """
    return (pattern.find('-') + 1, pattern.rfind('-') + 1)


def get_a(model, theta, r):
    """Return `a` values from model."""
    return tuple(a_ij for _, a_ij in sorted(model(theta, r).items()))


def poisson(a, y):
    return y * np.log(a) - a


def likelihood(model, ys_, theta, r):
    """L(theta | y) = sum_{i,j} y_ij * ln( a_ij(theta) ) - a_ij(theta)"""
    # ys_ is morphed
    # Note: do not morph `a`!!!
    a = get_a(model, theta, r)
    return sum(starmap(poisson, zip(a, ys_)))


class Worker:
    def __init__(self, model, ys, theta0, theta_bounds, r, method, options):
        self.model = model
        self.ys = ys
        self.theta0 = theta0
        self.theta_bounds = theta_bounds
        self.r = r
        self.method = method
        self.options = options

    def __call__(self, perm):
        result = minimize(lambda theta: -likelihood(self.model, morph10(self.ys, perm), theta, self.r),
                          self.theta0, bounds=self.theta_bounds, method=self.method, options=self.options)
        return perm, result

    def ignore_sigint():
        def sigint_handler(signum, frame):
            pass

        signal.signal(signal.SIGINT, sigint_handler)
