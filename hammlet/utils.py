__all__ = ('all_models', 'morph4', 'morph10', 'ij2pattern', 'pattern2ij',
           'get_model_theta_bounds', 'get_model_func', 'get_a', 'likelihood', 'Worker')

import re
import signal
from itertools import starmap

import click
import numpy as np
from scipy.optimize import minimize

all_models = tuple('1P1 1P2 1T1 1T2 1PH1 1PH2 1H1 1H2 1H3 1H4 1HP PL1 '
                   '2H1 2P1 2P2 2PH1 2PH2 2T1 2T2 2HP 2HA 2HB 2H2 PL2'.split())

regex_model1 = re.compile(r'1(?:P|T|PH)[12]|1H[P1-4]|2H1|PL1')
regex_model2 = re.compile(r'2(?:P|PH|T)[12]|2H[PAB2]|PL2')


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

    return [A[permutation[i], permutation[j]] for i in range(4) for j in range(i, 4)]


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


def get_model_theta_bounds(model_name):
    n0 = (0, 1000)
    T1 = (0, 10)
    T3 = (0, 10)
    gamma1 = (0, 1)
    gamma3 = (0, 1)
    if model_name in '1P1 1PH1 2P1 2PH1'.split():
        T1 = (0, 0)
    if model_name in '1P2 1PH2 1HP 2P2 2PH2 2HP'.split():
        T3 = (0, 0)
    if model_name in '1P1 1P2 1T2 1PH1 1H3 2P1 2P2 2PH1 2T1 2T2 2HB'.split():
        gamma1 = (0, 0)
    if model_name in '1T1 1H2'.split():
        gamma1 = (1, 1)
    if model_name in '1P1 1P2 1T1 1T2 1PH2 1H1 2P1 2P2 2PH2 2T2 2HA'.split():
        gamma3 = (0, 0)
    if model_name in '1H4 2T1'.split():
        gamma3 = (1, 1)
    if model_name in 'PL1 PL2'.split():
        T1 = (0, 0)
        T3 = (0, 0)
        gamma1 = (0, 0)
        gamma3 = (0, 0)
    return (n0, T1, T3, gamma1, gamma3)


def get_model_func(model_name):
    """Return model function for given model name."""
    from . import models
    if regex_model1.match(model_name):
        return models.model1
    elif regex_model2.match(model_name):
        return models.model2
    else:
        raise click.BadParameter('unknown model name "{}"'.format(model_name))


def get_a(model_func, theta, r):
    """Return `a` values from model."""
    return [a_ij for _, a_ij in sorted(model_func(theta, r).items())]


def poisson(a, y):
    return y * np.log(a) - a


def likelihood(model_func, ys_, theta, r):
    """L(theta | y) = sum_{i,j} y_ij * ln( a_ij(theta) ) - a_ij(theta)"""
    # ys_ is morphed
    # Note: do not morph `a`!!!
    a = get_a(model_func, theta, r)
    return sum(starmap(poisson, zip(a, ys_)))


class Worker:
    def __init__(self, model_func, ys, theta0, theta_bounds, r, method, options):
        self.model_func = model_func
        self.ys = ys
        self.theta0 = theta0
        self.theta_bounds = theta_bounds
        self.r = r
        self.method = method
        self.options = options

    def __call__(self, perm):
        result = minimize(lambda theta: -likelihood(self.model_func, morph10(self.ys, perm), theta, self.r),
                          self.theta0, bounds=self.theta_bounds, method=self.method, options=self.options)
        return perm, result

    def ignore_sigint():
        def sigint_handler(signum, frame):
            pass

        signal.signal(signal.SIGINT, sigint_handler)
