__all__ = ('fix', 'ij2pattern', 'pattern2ij', 'get_model_theta_bounds',
           'get_model_func', 'get_all_a', 'likelihood', 'Worker')

import re

import click
import numpy as np
from scipy.optimize import minimize

regex_model1 = re.compile(r'1(?:P|T|PH)[12]|1H[P1-4]|2H1')
regex_model2 = re.compile(r'2(?:P|PH|T)[12]|2H[PAB2]')


def fix(iterable, permutation):
    """Return fixed iterable according to given permutation.

    Examples:
        fix('-+++', (1,0,2,3)) -> '+-++'
        fix('+--+', (0,2,3,1)) -> '+-+-'
        fix(['Dog','Cow','Horse','Bat'], (1,2,3,0)) -> ['Cow','Horse','Bat','Dog']
        fix(['Human','Colugo','Tupaia','Mouse'], (1,2,0,3)) -> ['Colugo','Tupaia','Human','Mouse']
    """
    if permutation is None:
        return iterable
    if isinstance(iterable, str):
        return ''.join(iterable[i] for i in permutation)
    elif isinstance(iterable, list):
        return list(iterable[i] for i in permutation)
    elif isinstance(iterable, tuple):
        return tuple(iterable[i] for i in permutation)
    else:
        raise ValueError(f'Iterable type <{type(iterable)}> is not supported')


def ij2pattern(i, j):
    """Convert (i,j) pair into string pattern.

    Examples:
        ij2pattern(1, 1) -> "-+++"
        ij2pattern(2, 3) -> "+--+"
        ij2pattern(1, 4) -> "-++-"
        ij2pattern(4, 4) -> "+++-"
    """
    return ''.join('-' if t + 1 in (i, j) else '+' for t in range(4))


def pattern2ij(pattern):
    """Convert string pattern into (i,j) pair.

    Examples:
        pattern2ij("-+++") -> (1, 1)
        pattern2ij("+--+") -> (2, 3)
        pattern2ij("-++-") -> (1, 4)
        pattern2ij("+++-") -> (4, 4)
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
    return (n0, T1, T3, gamma1, gamma3)


def get_model_func(model_name):
    """Return model function for given model name."""
    from . import models
    if regex_model1.match(model_name):
        return models.model1
    elif regex_model2.match(model_name):
        return models.model2
    else:
        raise click.BadParameter(f'unknown model name "{model_name}"')


def get_all_a(model_func, permutation, theta, r):
    # return {fix(ij2pattern(i, j), permutation): a_ij
    #         for (i, j), a_ij in globals()[f'model{model}'](theta, r).items()}
    return {fix(ij2pattern(i, j), permutation): a_ij
            for (i, j), a_ij in model_func(theta, r).items()}


def poisson(a, y):
    return y * np.log(a) - a


def likelihood(model_func, data, permutation, theta, r):
    """L(theta | y) = sum_{i,j} y_ij * ln( a_ij(theta) ) - a_ij(theta)"""
    a = get_all_a(model_func, permutation, theta, r)  # a :: {pattern: a_ij}
    return sum(poisson(a[pattern], y_ij) for pattern, y_ij in data.items())


class Worker:
    def __init__(self, model_func, data, r, theta0, theta_bounds, method, options):
        self.model_func = model_func
        self.data = data
        self.r = r
        self.theta0 = theta0
        self.theta_bounds = theta_bounds
        self.method = method
        self.options = options

    def __call__(self, permutation):
        result = minimize(lambda theta: -likelihood(self.model_func, self.data, permutation, theta, self.r),
                          self.theta0, bounds=self.theta_bounds, method=self.method, options=self.options)
        return permutation, result
