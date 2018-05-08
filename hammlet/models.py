from __future__ import division

__all__ = ('all_models', 'models_H1', 'models_H2', 'models_mapping')

from collections import OrderedDict

import numpy as np


def ensure_interval(x):
    if isinstance(x, (int, float)):
        return (x, x)
    return tuple(x)


def summarize_a(a, n0, r):
    """a = n0 * (a0 + r1*a1 + r2*r2 + r3*a3 + r4*a4)"""
    return n0 * (a[0] + sum(ri * ai for ri, ai in zip(r, a[1:])))


class Model(object):

    mapping = OrderedDict()

    def __init__(self, name, n0=(0, 1000), T1=(0, 10), T3=(0, 10), gamma1=(0, 1), gamma3=(0, 1)):
        self.name = name
        self.n0_bounds = ensure_interval(n0)
        self.T1_bounds = ensure_interval(T1)
        self.T3_bounds = ensure_interval(T3)
        self.gamma1_bounds = ensure_interval(gamma1)
        self.gamma3_bounds = ensure_interval(gamma3)
        self.mapping[name] = self

    @property
    def bounds(self):
        return (self.n0_bounds, self.T1_bounds, self.T3_bounds, self.gamma1_bounds, self.gamma3_bounds)

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '{}(name={}, n0={}, T1={}, T3={}, gamma1={}, gamma3={})'.format(self.__class__.__name__,
                                                                               self.name,
                                                                               self.n0_bounds,
                                                                               self.T1_bounds,
                                                                               self.T3_bounds,
                                                                               self.gamma1_bounds,
                                                                               self.gamma3_bounds)


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


models_H1 = (ModelH1('PL1', T1=0, T3=0, gamma1=0, gamma3=0),
             ModelH1('1P1', T1=0, gamma1=0, gamma3=0),
             ModelH1('1P2', T3=0, gamma1=0, gamma3=0),
             ModelH1('1T1', gamma1=1, gamma3=0),
             ModelH1('1T2', gamma1=0, gamma3=0),
             ModelH1('1PH1', T1=0, gamma1=0),
             ModelH1('1PH2', T3=0, gamma3=0),
             ModelH1('1H1', gamma3=0),
             ModelH1('1H2', gamma1=1),
             ModelH1('1H3', gamma1=0),
             ModelH1('1H4', gamma3=1),
             ModelH1('2H1'))
models_H2 = (ModelH2('PL2', T1=0, T3=0, gamma1=0, gamma3=0),
             ModelH2('2P1', T1=0, gamma1=0, gamma3=0),
             ModelH2('2P2', T3=0, gamma1=0, gamma3=0),
             ModelH2('2T1', gamma1=0, gamma3=1),
             ModelH2('2T2', gamma1=0, gamma3=0),
             ModelH2('2PH1', T1=0, gamma1=0),
             ModelH2('2PH2', T3=0, gamma3=0),
             ModelH2('2HP', T3=0),
             ModelH2('2HA1', gamma3=0),
             ModelH2('2HA2', gamma3=1),
             ModelH2('2HB1', gamma1=0),
             ModelH2('2HB2', gamma1=1),
             ModelH2('2H2'))
all_models = models_H1 + models_H2

models_mapping = Model.mapping
