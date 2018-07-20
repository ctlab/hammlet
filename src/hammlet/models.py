from __future__ import division

from collections import OrderedDict

import numpy as np

__all__ = ['all_models', 'models_H1', 'models_H2', 'models_hierarchy',
           'models_mapping', 'models_mapping_mnemonic']


class CaseInsensitiveOrderedDict(OrderedDict):

    class Key(str):
        def __init__(self, key):
            str.__init__(key)

        def __hash__(self):
            return hash(self.lower())

        def __eq__(self, other):
            return self.lower() == other.lower()

    def __init__(self, items=None):
        super(CaseInsensitiveOrderedDict, self).__init__()
        if items is None:
            items = []
        for key, val in items:
            self[key] = val

    def __contains__(self, key):
        key = self.Key(key)
        return super(CaseInsensitiveOrderedDict, self).__contains__(key)

    def __setitem__(self, key, value):
        key = self.Key(key)
        super(CaseInsensitiveOrderedDict, self).__setitem__(key, value)

    def __getitem__(self, key):
        key = self.Key(key)
        return super(CaseInsensitiveOrderedDict, self).__getitem__(key)


def get_mnemo_name(T1, T3, gamma1, gamma3):
    """
    >>> get_mnemo_name((0, 10), (0, 10), (0, 1), (0, 1))
    'TTgg'
    >>> get_mnemo_name(0, (0, 10), 1, None)
    '0T1N'
    """
    def _T(x):
        if x == 0 or x == (0, 0):
            return '0'
        return 'T'

    def _G(x):
        if x is None:
            return 'N'
        if x == 0 or x == (0, 0):
            return '0'
        if x == 1 or x == (1, 1):
            return '1'
        return 'g'

    return _T(T1) + _T(T3) + _G(gamma1) + _G(gamma3)


def ensure_interval(x):
    """
    >>> ensure_interval(1)
    (1, 1)
    >>> ensure_interval(0.2)
    (0.2, 0.2)
    >>> ensure_interval((0.2, 0.8))
    (0.2, 0.8)
    >>> ensure_interval([0.3, 0.5])
    (0.3, 0.5)
    """
    if x is None:
        return (0, 0)
    if isinstance(x, (int, float)):
        return (x, x)
    return tuple(x)


def summarize_a(a, n0, r):
    """a = n0 * (a0 + r1*a1 + r2*r2 + r3*a3 + r4*a4)

    >>> round(summarize_a((0.15, 0.04, 0.05, 0, 0.05), 97.2, (1,1,1,1)), 3)
    28.188
    >>> round(summarize_a((0.21, 0, 0.01, 0, 0.003), 96.8, (1,1,1,1)), 4)
    21.5864
    """
    return n0 * (a[0] + sum(ri * ai for ri, ai in zip(r, a[1:])))


class Model(object):

    mapping = OrderedDict()  # {name: model} :: {str: Model}
    mapping_mnemonic = CaseInsensitiveOrderedDict()  # {mnemonic_name: model} :: {str: Model}

    def __init__(self, name, n0=(0, 1000), T1=(0, 10), T3=(0, 10), gamma1=(0, 1), gamma3=(0, 1)):
        self.name = name
        self.mnemonic_name = get_mnemo_name(T1, T3, gamma1, gamma3)
        self.n0_bounds = ensure_interval(n0)
        self.T1_bounds = ensure_interval(T1)
        self.T3_bounds = ensure_interval(T3)
        self.gamma1_bounds = ensure_interval(gamma1)
        self.gamma3_bounds = ensure_interval(gamma3)
        self.mapping[name] = self.mapping_mnemonic[self.mnemonic_name] = self

    @property
    def bounds(self):
        return (
            self.n0_bounds,
            self.T1_bounds,
            self.T3_bounds,
            self.gamma1_bounds,
            self.gamma3_bounds,
        )

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '{}(name={!r}, n0={}, T1={}, T3={}, gamma1={}, gamma3={})'.format(
            self.__class__.__name__,
            self.name,
            self.n0_bounds,
            self.T1_bounds,
            self.T3_bounds,
            self.gamma1_bounds,
            self.gamma3_bounds
        )


class ModelH1(Model):
    @staticmethod
    def __call__(theta, r):
        n0, T1, T3, gamma1, gamma3 = theta
        r1, r2, r3, r4 = r
        tau1 = T1 / r1
        tau2 = T1 / r2
        tau3 = T3 / r3
        tau4 = T3 / r4
        gamma2 = 1 - gamma1
        gamma4 = 1 - gamma3
        e1 = np.exp(-tau1)
        e2 = np.exp(-tau2)
        e3 = np.exp(-tau3)
        e4 = np.exp(-tau4)
        e14 = np.exp(-tau1 - tau4)
        e23 = np.exp(-tau2 - tau3)
        e24 = np.exp(-tau2 - tau4)
        e123 = np.exp(-tau1 - tau2 - tau3)
        e124 = np.exp(-tau1 - tau2 - tau4)
        e3_1 = np.exp(3 * -tau1)
        e3_14 = np.exp(3 * -tau1 - tau4)
        e3_23 = np.exp(3 * -tau2 - tau3)
        e3_24 = np.exp(3 * -tau2 - tau4)
        a = dict()

        a0 = 1 / 6 * gamma3 * gamma1**2 * e14 + gamma1 * (1 / 6 * gamma3 * (2 * e1 - 2 * e14) + 1 / 6 * gamma2 * gamma3 * (4 * e14 - 2 * e124) + 1 / 6 * gamma4 * (2 * e1 - e123)) + 1 / 6 * gamma2**2 * gamma3 * (e3_24 - 6 * e24 + 6 * e4) + gamma2 * (1 / 6 * gamma3 * (-4 * e2 + 4 * e24 - 6 * e4 + 6) + 1 / 6 * gamma4 * (-4 * e2 + e3_23 - 2 * e23 + 6))
        a1 = 0
        a2 = 1 / 6 * gamma3 * gamma2**2 * (6 * e4 * tau2 - e3_24 + 9 * e24 - 8 * e4) + gamma2 * (1 / 6 * gamma4 * (6 * tau2 + 6 * e2 - e3_23 + 3 * e23 - 2 * e3 - 6) + 1 / 6 * gamma3 * (-6 * e4 * tau2 + 6 * tau2 + 6 * e2 - 6 * e24 + 6 * e4 - 6))
        a3 = 0
        a4 = 0
        a[1, 1] = summarize_a((a0, a1, a2, a3, a4), n0, r)

        a0 = 1 / 6 * gamma3 * gamma1**2 * (2 * e14 - e3_14) + gamma1 * (1 / 6 * gamma3 * (4 * e1 - 4 * e14) + 1 / 3 * gamma2 * gamma3 * e124 + 1 / 6 * gamma4 * e123) + 1 / 6 * gamma2**2 * gamma3 * (2 * e24 - e3_24) + gamma2 * (1 / 6 * gamma3 * (4 * e2 - 4 * e24) + 1 / 6 * gamma4 * (2 * e23 - e3_23))
        a1 = 1 / 6 * gamma3 * gamma1**2 * (e4 * (e3_1 + 2) - 3 * e14) + 1 / 6 * gamma3 * gamma1 * (-6 * e1 + 6 * e14 - 6 * e4 + 6)
        a2 = 1 / 6 * gamma3 * gamma2**2 * (e3_24 - 3 * e24 + 2 * e4) + gamma2 * (1 / 6 * gamma4 * (e3_23 - 3 * e23 + 2 * e3) - gamma3 * (e2 - e24 + e4 - 1))
        a3 = 0
        a4 = gamma3 * (tau4 + e4 - 1)
        a[1, 2] = summarize_a((a0, a1, a2, a3, a4), n0, r)

        a0 = -1 / 6 * gamma3 * gamma1**2 * e14 + gamma1 * (1 / 3 * gamma3 * e14 + 1 / 6 * gamma2 * gamma3 * (2 * e124 - 4 * e14) + 1 / 6 * gamma4 * (e123 - 2 * e1)) + 1 / 6 * gamma2**2 * gamma3 * (-e3_24 + 6 * e24 - 6 * e4) + 1 / 6 * gamma4 * (6 - 4 * e23) + gamma2 * (1 / 6 * gamma3 * (6 * e4 - 4 * e24) + 1 / 6 * gamma4 * (4 * e2 - e3_23 + 2 * e23 - 6))
        a1 = 0
        a2 = 1 / 6 * gamma3 * gamma2**2 * (-6 * e4 * tau2 + e3_24 - 9 * e24 + 8 * e4) + gamma2 * (1 / 6 * gamma4 * (-6 * tau2 - 6 * e2 + e3_23 - 3 * e23 + 2 * e3 + 6) + 1 / 6 * gamma3 * (6 * (e24 - e4) + 6 * e4 * tau2)) + 1 / 6 * gamma4 * (6 * (e23 - e3) + 6 * tau2)
        a3 = gamma4 * (tau3 + e3 - 1)
        a4 = 0
        a[1, 3] = summarize_a((a0, a1, a2, a3, a4), n0, r)

        a0 = -1 / 6 * gamma3 * gamma1**2 * e14 + gamma1 * (1 / 3 * gamma3 * e14 + 1 / 6 * gamma2 * gamma3 * (2 * e124 - 4 * e14) + 1 / 6 * gamma4 * e123) + 1 / 6 * gamma2**2 * gamma3 * (-e3_24 + 6 * e24 - 6 * e4) + gamma2 * (1 / 6 * gamma3 * (6 * e4 - 4 * e24) + 1 / 6 * gamma4 * (2 * e23 - e3_23))
        a1 = 0
        a2 = 1 / 6 * gamma3 * gamma2**2 * (2 * e4 * (4 - 3 * tau2) + e3_24 - 9 * e24) + gamma2 * (1 / 6 * gamma4 * (e3_23 - 3 * e23 + 2 * e3) + gamma3 * (e4 * (tau2 - 1) + e24))
        a3 = 0
        a4 = 0
        a[1, 4] = summarize_a((a0, a1, a2, a3, a4), n0, r)

        a0 = 1 / 6 * gamma3 * gamma1**2 * (e3_14 - 6 * e14 + 6 * e4) + gamma1 * (1 / 6 * gamma3 * (-4 * e1 + 4 * e14 - 6 * e4 + 6) + 1 / 6 * gamma2 * gamma3 * (4 * e24 - 2 * e124) + 1 / 6 * gamma4 * (2 * e23 - e123)) + 1 / 6 * gamma2**2 * gamma3 * e24 + gamma2 * (1 / 6 * gamma3 * (2 * e2 - 2 * e24) + 1 / 6 * gamma4 * e23)
        a1 = 1 / 6 * gamma3 * gamma1**2 * (6 * e4 * tau1 - e3_14 + 9 * e14 - 8 * e4) + 1 / 6 * gamma3 * gamma1 * (-6 * e4 * tau1 + 6 * tau1 + 6 * e1 - 6 * e14 + 6 * e4 - 6)
        a2 = 0
        a3 = 0
        a4 = 0
        a[2, 2] = summarize_a((a0, a1, a2, a3, a4), n0, r)

        a0 = 1 / 6 * gamma3 * gamma1**2 * (-e3_14 + 6 * e14 - 6 * e4) + gamma1 * (1 / 6 * gamma3 * (6 * e4 - 4 * e14) + 1 / 6 * gamma2 * gamma3 * (2 * e124 - 4 * e24) + 1 / 6 * gamma4 * (e123 - 2 * e23)) - 1 / 6 * gamma2**2 * gamma3 * e24 + 1 / 3 * gamma4 * e23 + gamma2 * (1 / 3 * gamma3 * e24 - 1 / 6 * gamma4 * e23)
        a1 = 1 / 6 * gamma3 * gamma1**2 * e4 * (-6 * tau1 + e3_1 - 9 * e1 + 8) + 1 / 6 * gamma3 * gamma1 * e4 * (6 * (e1 - 1) + 6 * tau1)
        a2 = 0
        a3 = 0
        a4 = 0
        a[2, 3] = summarize_a((a0, a1, a2, a3, a4), n0, r)

        a0 = 1 / 6 * gamma3 * gamma1**2 * (-e3_14 + 6 * e14 - 6 * e4) + gamma1 * (1 / 6 * gamma3 * (6 * e4 - 4 * e14) + 1 / 6 * gamma2 * gamma3 * (2 * e124 - 4 * e24) + 1 / 6 * gamma4 * (-4 * e1 - 2 * e23 + e123 + 6)) - 1 / 6 * gamma2**2 * gamma3 * e24 + gamma2 * (1 / 3 * gamma3 * e24 + 1 / 6 * gamma4 * (2 * e2 - e23))
        a1 = gamma1 * (gamma3 * (e4 * (tau1 - 1) + e14) + gamma4 * (tau1 + e1 - 1)) - 1 / 6 * gamma1**2 * gamma3 * e4 * (6 * tau1 - e3_1 + 9 * e1 - 8)
        a2 = 0
        a3 = 0
        a4 = 0
        a[2, 4] = summarize_a((a0, a1, a2, a3, a4), n0, r)

        a0 = 1 / 2 * gamma3 * gamma1**2 * e14 + gamma1 * (-1 / 3 * gamma3 * e14 + 1 / 6 * gamma2 * gamma3 * (4 * e14 + 4 * e24 - 2 * e124) + 1 / 6 * gamma4 * (2 * e1 + 2 * e23 - e123)) + 1 / 2 * gamma2**2 * gamma3 * e24 - 1 / 3 * gamma4 * e23 + gamma2 * (1 / 6 * gamma4 * (2 * e2 + e23) - 1 / 3 * gamma3 * e24)
        a1 = 0
        a2 = 0
        a3 = 0
        a4 = 0
        a[3, 3] = summarize_a((a0, a1, a2, a3, a4), n0, r)

        a0 = -1 / 2 * gamma3 * gamma1**2 * e14 + gamma1 * (1 / 6 * gamma3 * (2 * e1 + 2 * e14) + 1 / 6 * gamma2 * gamma3 * (-4 * e14 - 4 * e24 + 2 * e124) + 1 / 6 * gamma4 * (e123 - 2 * e23)) - 1 / 2 * gamma2**2 * gamma3 * e24 + 1 / 3 * gamma4 * e23 + gamma2 * (1 / 3 * gamma3 * (e2 + e24) - 1 / 6 * gamma4 * e23)
        a1 = 0
        a2 = 0
        a3 = 0
        a4 = 0
        a[3, 4] = summarize_a((a0, a1, a2, a3, a4), n0, r)

        a0 = 1 / 2 * gamma3 * gamma1**2 * e14 + gamma1 * (-1 / 3 * gamma3 * e14 + 1 / 6 * gamma2 * gamma3 * (4 * e14 + 4 * e24 - 2 * e124) + 1 / 6 * gamma4 * (2 * e23 - e123)) + 1 / 2 * gamma2**2 * gamma3 * e24 + gamma2 * (1 / 6 * gamma4 * e23 - 1 / 3 * gamma3 * e24)
        a1 = 0
        a2 = 0
        a3 = 0
        a4 = 0
        a[4, 4] = summarize_a((a0, a1, a2, a3, a4), n0, r)

        return a


class ModelH2(Model):
    @staticmethod
    def __call__(theta, r):
        n0, T1, T3, gamma1, gamma3 = theta
        r1, r2, r3, r4 = r
        tau1 = T1 / r1
        tau2 = T1 / r2
        tau3 = T3 / r3
        tau4 = T3 / r4
        gamma2 = 1 - gamma1
        gamma4 = 1 - gamma3
        e1 = np.exp(-tau1)
        e2 = np.exp(-tau2)
        e3 = np.exp(-tau3)
        e4 = np.exp(-tau4)
        e14 = np.exp(-tau1 - tau4)
        e23 = np.exp(-tau2 - tau3)
        e123 = np.exp(-tau1 - tau2 - tau3)
        e124 = np.exp(-tau1 - tau2 - tau4)
        e3_1 = np.exp(3 * -tau1)
        e3_2 = np.exp(3 * -tau2)
        e3_14 = np.exp(3 * -tau1 - tau4)
        e3_23 = np.exp(3 * -tau2 - tau3)
        a = dict()

        a0 = gamma2 * (1 / 6 * gamma3 * (2 * e14 - e124) + 1 / 6 * gamma4 * (-4 * e2 + e3_23 - 2 * e23 + 6)) + gamma1 * (1 / 6 * gamma3 * e14 + 1 / 6 * gamma4 * (2 * e1 - e123))
        a1 = 0
        a2 = 1 / 6 * gamma2 * gamma4 * (6 * tau2 + 6 * e2 - e3_23 + 3 * e23 - 2 * e3 - 6)
        a3 = 0
        a4 = 0
        a[1, 1] = summarize_a((a0, a1, a2, a3, a4), n0, r)

        a0 = gamma1 * (1 / 6 * gamma3 * (2 * e14 - e3_14) + 1 / 6 * gamma4 * e123) + gamma2 * (1 / 6 * gamma3 * e124 + 1 / 6 * gamma4 * (2 * e23 - e3_23))
        a1 = 1 / 6 * gamma1 * gamma3 * e4 * (e3_1 - 3 * e1 + 2)
        a2 = 1 / 6 * gamma2 * gamma4 * e3 * (e3_2 - 3 * e2 + 2)
        a3 = 0
        a4 = 0
        a[1, 2] = summarize_a((a0, a1, a2, a3, a4), n0, r)

        a0 = gamma2 * (1 / 6 * gamma3 * e124 + 1 / 6 * gamma4 * (4 * e2 - e3_23 - 2 * e23)) + gamma1 * (1 / 6 * gamma3 * e14 + 1 / 6 * gamma4 * (-2 * e1 - 4 * e23 + e123 + 6))
        a1 = 0
        a2 = 1 / 6 * gamma2 * gamma4 * (-6 * e2 + e3_23 + 3 * e23 - 4 * e3 + 6) + gamma1 * gamma4 * (tau2 + e23 - e3)
        a3 = gamma1 * gamma4 * (tau3 + e3 - 1) + gamma2 * gamma4 * (tau3 + e3 - 1)
        a4 = 0
        a[1, 3] = summarize_a((a0, a1, a2, a3, a4), n0, r)

        a0 = gamma1 * (1 / 6 * gamma3 * (2 * e1 - e14) + 1 / 6 * gamma4 * e123) + gamma2 * (1 / 6 * gamma3 * (-4 * e2 - 2 * e14 + e124 + 6) + 1 / 6 * gamma4 * (2 * e23 - e3_23))
        a1 = 0
        a2 = gamma2 * (1 / 6 * gamma4 * (e3_23 - 3 * e23 + 2 * e3) + gamma3 * (tau2 + e2 - 1))
        a3 = 0
        a4 = 0
        a[1, 4] = summarize_a((a0, a1, a2, a3, a4), n0, r)

        a0 = gamma2 * (1 / 6 * gamma3 * (2 * e2 - e124) + 1 / 6 * gamma4 * e23) + gamma1 * (1 / 6 * gamma3 * (-4 * e1 + e3_14 - 2 * e14 + 6) + 1 / 6 * gamma4 * (2 * e23 - e123))
        a1 = 1 / 6 * gamma1 * gamma3 * (3 * e1 * (e4 + 2) - e3_14 - 2 * e4 + 6 * tau1 - 6)
        a2 = 0
        a3 = 0
        a4 = 0
        a[2, 2] = summarize_a((a0, a1, a2, a3, a4), n0, r)

        a0 = gamma2 * (1 / 6 * gamma3 * (-2 * e2 - 4 * e14 + e124 + 6) + 1 / 6 * gamma4 * e23) + gamma1 * (1 / 6 * gamma3 * (4 * e1 - e3_14 - 2 * e14) + 1 / 6 * gamma4 * e123)
        a1 = 1 / 6 * gamma1 * gamma3 * (e4 * (e3_1 - 4) + 3 * e1 * (e4 - 2) + 6) + gamma2 * gamma3 * (e4 * (e1 - 1) + tau1)
        a2 = 0
        a3 = 0
        a4 = gamma1 * gamma3 * (tau4 + e4 - 1) + gamma2 * gamma3 * (tau4 + e4 - 1)
        a[2, 3] = summarize_a((a0, a1, a2, a3, a4), n0, r)

        a0 = gamma2 * (1 / 6 * gamma3 * e124 + 1 / 6 * gamma4 * (2 * e2 - e23)) + gamma1 * (1 / 6 * gamma3 * (2 * e14 - e3_14) + 1 / 6 * gamma4 * (-4 * e1 - 2 * e23 + e123 + 6))
        a1 = gamma1 * (1 / 6 * gamma3 * e4 * (e3_1 - 3 * e1 + 2) + gamma4 * (tau1 + e1 - 1))
        a2 = 0
        a3 = 0
        a4 = 0
        a[2, 4] = summarize_a((a0, a1, a2, a3, a4), n0, r)

        a0 = gamma2 * (1 / 6 * gamma3 * (2 * e2 - e124) + 1 / 6 * gamma4 * (2 * e2 - e23)) + gamma1 * (1 / 6 * gamma3 * (2 * e1 - e14) + 1 / 6 * gamma4 * (2 * e1 - e123))
        a1 = 0
        a2 = 0
        a3 = 0
        a4 = 0
        a[3, 3] = summarize_a((a0, a1, a2, a3, a4), n0, r)

        a0 = gamma2 * (1 / 6 * gamma3 * e124 + 1 / 6 * gamma4 * e23) + gamma1 * (1 / 6 * gamma3 * e14 + 1 / 6 * gamma4 * e123)
        a1 = 0
        a2 = 0
        a3 = 0
        a4 = 0
        a[3, 4] = summarize_a((a0, a1, a2, a3, a4), n0, r)

        a0 = gamma2 * (1 / 6 * gamma3 * (2 * e14 - e124) + 1 / 6 * gamma4 * e23) + gamma1 * (1 / 6 * gamma3 * e14 + 1 / 6 * gamma4 * (2 * e23 - e123))
        a1 = 0
        a2 = 0
        a3 = 0
        a4 = 0
        a[4, 4] = summarize_a((a0, a1, a2, a3, a4), n0, r)

        return a


# Note: first model in list must be the most complex, last model must be the simplest
models_H1 = (
    ModelH1('2H1'),
    ModelH1('1H1', gamma3=0),
    ModelH1('1H2', gamma1=1),
    ModelH1('1H3', gamma1=0),
    ModelH1('1H4', gamma3=1),
    ModelH1('1HP', T3=0),
    ModelH1('1T1', gamma1=1, gamma3=0),
    ModelH1('1T2', gamma1=0, gamma3=0),
    ModelH1('1T2A', gamma1=0, gamma3=1),
    ModelH1('1T2B', gamma1=1, gamma3=1),
    ModelH1('1PH1', T1=0, gamma1=None),
    ModelH1('1PH1A', T3=0, gamma1=1),
    ModelH1('1PH2', T3=0, gamma3=0),
    ModelH1('1PH3', T3=0, gamma3=1),
    ModelH1('1P1', T1=0, gamma1=None, gamma3=0),
    ModelH1('1P2', T3=0, gamma1=0, gamma3=None),
    ModelH1('1P2A', T1=0, gamma1=None, gamma3=1),
    ModelH1('1P2B', T3=0, gamma1=1, gamma3=1),
    ModelH1('1P3', T3=0, gamma1=1, gamma3=0),
    ModelH1('PL1', T1=0, T3=0, gamma1=None, gamma3=None),
)
models_H2 = (
    ModelH2('2H2'),
    ModelH2('2HA1', gamma3=0),
    ModelH2('2HA2', gamma3=1),
    ModelH2('2HB1', gamma1=0),
    ModelH2('2HB2', gamma1=1),
    ModelH2('2HP', T3=0),
    ModelH2('2T1', gamma1=0, gamma3=1),
    ModelH2('2T2', gamma1=0, gamma3=0),
    ModelH2('2T2A', gamma1=0, gamma3=1),
    ModelH2('2T2B', gamma1=1, gamma3=1),
    ModelH2('2PH1', T1=0, gamma1=None),
    ModelH2('2PH2', T3=0, gamma3=0),
    ModelH2('2PH2A', T3=0, gamma1=0),
    ModelH2('2PH2B', T3=0, gamma1=1),
    ModelH2('2PH2C', T3=0, gamma3=1),
    ModelH2('2P1', T1=0, gamma1=None, gamma3=0),
    ModelH2('2P1A', T1=0, gamma1=None, gamma3=1),
    ModelH2('2P2', T3=0, gamma1=0, gamma3=0),
    ModelH2('2P2A', T3=0, gamma1=1, gamma3=1),
    ModelH2('2P3', T3=0, gamma1=1, gamma3=0),
    ModelH2('2P3A', T3=0, gamma1=0, gamma3=1),
    ModelH2('PL2', T1=0, T3=0, gamma1=None, gamma3=None),
)
all_models = models_H1 + models_H2

models_mapping = Model.mapping
models_mapping_mnemonic = Model.mapping_mnemonic

models_hierarchy = {
    'H1': {
        'free': {
            '2H1': '1H1 1H2 1H3 1H4 1HP'.split(),
            '1H1': '1T1 1T2 1PH1 1PH2 1PH3'.split(),
            '1H2': '1T1 1T2 1PH1 1PH2 1PH3'.split(),
            '1H3': '1T1 1T2 1PH1 1PH2 1PH3'.split(),
            '1H4': '1T1 1T2 1PH1 1PH2 1PH3'.split(),
            '1HP': '1T1 1T2 1PH1 1PH2 1PH3'.split(),
            '1T1': '1P1 1P2 1P3'.split(),
            '1T2': '1P1 1P2 1P3'.split(),
            '1PH1': '1P1 1P2 1P3'.split(),
            '1PH2': '1P1 1P2 1P3'.split(),
            '1PH3': '1P1 1P2 1P3'.split(),
            '1P1': 'PL1'.split(),
            '1P2': 'PL1'.split(),
            '1P3': 'PL1'.split(),
        },
        'non-free': {
            '2H1': '1H1 1H2 1H3 1H4 1HP 1PH1'.split(),
            '1H1': '1T1 1T2 1P1 1PH2'.split(),
            '1H2': '1PH1 1T2B 1T1 1PH1A'.split(),
            '1H3': '1T2A 1T2 1PH1 1P2'.split(),
            '1H4': '1T2B 1T2A 1PH3 1P2A'.split(),
            '1HP': 'PL1 1P2 1PH2 1PH3 1PH1A'.split(),
            '1T1': '1P1 1P3'.split(),
            '1T2': '1P1 1P2'.split(),
            '1T2A': '1P2 1P2A'.split(),
            '1T2B': '1P2A 1P2B'.split(),
            '1PH1': '1P2A PL1'.split(),
            '1PH1A': '1P2B 1P3 PL1'.split(),
            '1PH2': '1P2 1P3 PL1'.split(),
            '1PH3': '1P2 1P2B PL1'.split(),
            '1P1': 'PL1'.split(),
            '1P2': 'PL1'.split(),
            '1P2A': 'PL1'.split(),
            '1P2B': 'PL1'.split(),
            '1P3': 'PL1'.split(),
        }
    },
    'H2': {
        'free': {
            '2H2': '2HA1 2HB1 2HP'.split(),
            '2HA1': '2T1 2T2 2PH1 2PH2'.split(),
            '2HB1': '2T1 2T2 2PH1 2PH2'.split(),
            '2HP': '2T1 2T2 2PH1 2PH2'.split(),
            '2T1': '2P1 2P2 2P3'.split(),
            '2T2': '2P1 2P2 2P3'.split(),
            '2PH1': '2P1 2P2 2P3'.split(),
            '2PH2': '2P1 2P2 2P3'.split(),
            '2P1': 'PL2'.split(),
            '2P2': 'PL2'.split(),
            '2P3': 'PL2'.split(),
        },
        'non-free': {
            '2H2': '2HA1 2HA2 2HB1 2HB2 2HP'.split(),
            '2HA1': '2PH2 2T2 2T1'.split(),
            '2HA2': '2P1A 2T2B 2T2A 2PH2C'.split(),
            '2HB1': '2T2A 2PH1 2PH2B 2PH2A'.split(),
            '2HB2': '2T1 2T2B 2PH1 2PH2B'.split(),
            '2HP': '2PH2 2PH2A 2PH2B 2PH2C PL2'.split(),
            '2T1': '2P3 2P1'.split(),
            '2T2': '2P1 2P2'.split(),
            '2T2A': '2P1A 2P3A'.split(),
            '2T2B': '2P1A 2P2A'.split(),
            '2PH1': '2P1 2P1A PL2'.split(),
            '2PH2': '2P2 2P3 PL2'.split(),
            '2PH2A': '2P2 2P3A PL2'.split(),
            '2PH2B': '2P1 2P3'.split(),
            '2PH2C': '2P2A 2P3A'.split(),
            '2P1': 'PL2'.split(),
            '2P1A': 'PL2'.split(),
            '2P2': 'PL2'.split(),
            '2P2A': 'PL2'.split(),
            '2P3': 'PL2'.split(),
            '2P3A': 'PL2'.split(),
        }
    }
}
