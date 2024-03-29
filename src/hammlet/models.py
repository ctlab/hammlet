from __future__ import division

import re
import sys
from abc import abstractmethod
from collections import OrderedDict

import numpy as np

__all__ = [
    "all_models",
    "models_H1",
    "models_H2",
    "models_mapping",
    "models_mapping_mnemonic",
]

if sys.version < "3":
    # Python 2 has no re.fullmatch
    def fullmatch(regex, string, flags=0):
        """Emulate python-3.4 re.fullmatch()."""
        return re.match("(?:" + regex + r")\Z", string, flags=flags)

    re.fullmatch = fullmatch


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


def constraint_bounds(xs, low, high):
    """
    >>> constraint_bounds((0, 10), 1, 5)
    (1, 5)
    >>> constraint_bounds((5, 10), 0, 20)
    (5, 10)
    >>> constraint_bounds((0, 10), 1, None)
    (1, 10)
    >>> constraint_bounds((0, 10), None, 8)
    (0, 8)
    """
    if xs is None:
        xs = (None, None)
    a, b = xs
    if low is not None:
        if a is None or a < low:
            a = low
    if high is not None:
        if b is None or b > high:
            b = high
    return (a, b)


def constraint_value(x, bounds):
    """
    >>> constraint_value(42, (0, 50))
    42
    >>> constraint_value(42, (0, 10))
    10
    >>> constraint_value(10, (42, 50))
    42
    >>> constraint_value(42, (0, None))
    42
    >>> constraint_value(42, (None, 50))
    42
    >>> constraint_value(42, None)
    42
    """
    assert x is not None
    if bounds is None:
        return x
    low, high = bounds
    if low is not None and x < low:
        x = low
    if high is not None and x > high:
        x = high
    return x


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
    if isinstance(x, (int, float)):
        return (x, x)
    return tuple(x)


def summarize_a(a, r, n0):
    """Returns `n0 * (a0 + r1*a1 + r2*a2 + r3*a3 + r4*a4)`

    >>> round(summarize_a((0.75, 0.2, 0.05, 0.11, 0.051), (1,1,1,1), 100), 1)
    116.1
    >>> round(summarize_a((0.2, 0, 0.063, 0, 0.03), (1,1,1,1), 50), 2)
    14.65
    """
    a0, a1, a2, a3, a4 = a
    r1, r2, r3, r4 = r
    return n0 * (a0 + r1 * a1 + r2 * a2 + r3 * a3 + r4 * a4)


class Model(object):

    mapping = CaseInsensitiveOrderedDict()  # {name: Model}
    mapping_mnemonic = CaseInsensitiveOrderedDict()  # {name: Model}

    __slots__ = (
        "name",
        "mnemonic_name",
        "perms",
        "n0_bounds",
        "T1_bounds",
        "T3_bounds",
        "gamma1_bounds",
        "gamma3_bounds",
    )

    def __init__(self, name, mnemonic_name, perms="all"):
        assert re.fullmatch(
            r"H[12]:[T01]{2}[g01Nn]{2}", mnemonic_name
        ), "Bad mnemonic_name '{}'".format(mnemonic_name)
        assert name not in self.mapping, "Duplicate name '{}'".format(name)
        assert (
            mnemonic_name not in self.mapping_mnemonic
        ), "Duplicate mnemonic_name '{}'".format(mnemonic_name)

        def to_bound(c):
            if c == "T":
                return (0, None)
            elif c == "g":
                return (0, 1)
            elif c == "0":
                return (0, 1e-9)
            elif c == "1":
                return (1 - 1e-9, 1)
            elif c == "N" or c == "n":
                return None
            else:
                raise ValueError("Bad symbol in mnemonic name: '{}'".format(c))

        group, mnemo = mnemonic_name.split(":")

        self.name = name
        self.mnemonic_name = mnemonic_name
        self.perms = perms
        self.n0_bounds = (0, None)
        self.T1_bounds = to_bound(mnemo[0])
        self.T3_bounds = to_bound(mnemo[1])
        self.gamma1_bounds = to_bound(mnemo[2])
        self.gamma3_bounds = to_bound(mnemo[3])

        self.mapping[self.name] = self
        self.mapping_mnemonic[self.mnemonic_name] = self

    @property
    def bounds(self):
        return (
            self.n0_bounds,
            self.T1_bounds,
            self.T3_bounds,
            self.gamma1_bounds,
            self.gamma3_bounds,
        )

    def get_safe_bounds(
        self, n0_low=1e-12, n0_high=1000, T_low=0, T_high=10, gamma_low=0, gamma_high=1
    ):
        n0 = constraint_bounds(self.n0_bounds, n0_low, n0_high)
        T1 = constraint_bounds(self.T1_bounds, T_low, T_high)
        T3 = constraint_bounds(self.T3_bounds, T_low, T_high)
        gamma1 = constraint_bounds(self.gamma1_bounds, gamma_low, gamma_high)
        gamma3 = constraint_bounds(self.gamma3_bounds, gamma_low, gamma_high)

        return (n0, T1, T3, gamma1, gamma3)

    def apply_bounds(self, theta):
        return tuple(map(constraint_value, theta, self.bounds))

    def get_full_mnemonic_name(self):
        if isinstance(self, ModelH1):
            return "H1:" + self.mnemonic_name
        elif isinstance(self, ModelH2):
            return "H2:" + self.mnemonic_name
        else:
            raise ValueError("Model is neither H1 nor H2")

    @abstractmethod
    def __call__(self, theta, r):
        pass

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __str__(self):
        return self.name

    def __repr__(self):
        return "{}(name={!r}, n0={}, T1={}, T3={}, gamma1={}, gamma3={})".format(
            self.__class__.__name__,
            self.name,
            self.n0_bounds,
            self.T1_bounds,
            self.T3_bounds,
            self.gamma1_bounds,
            self.gamma3_bounds,
        )


class ModelH1(Model):
    def __init__(self, name, mnemo, perms="all"):
        mnemonic_name = "H1:" + mnemo
        super(ModelH1, self).__init__(name, mnemonic_name, perms)

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

        # fmt: off
        a0 = 1 / 6 * gamma3 * gamma1**2 * e14 + gamma1 * (1 / 6 * gamma3 * (2 * e1 - 2 * e14) + 1 / 6 * gamma2 * gamma3 * (4 * e14 - 2 * e124) + 1 / 6 * gamma4 * (2 * e1 - e123)) + 1 / 6 * gamma2**2 * gamma3 * (e3_24 - 6 * e24 + 6 * e4) + gamma2 * (1 / 6 * gamma3 * (-4 * e2 + 4 * e24 - 6 * e4 + 6) + 1 / 6 * gamma4 * (-4 * e2 + e3_23 - 2 * e23 + 6))
        a1 = 0
        a2 = 1 / 6 * gamma3 * gamma2**2 * (6 * e4 * tau2 - e3_24 + 9 * e24 - 8 * e4) + gamma2 * (1 / 6 * gamma4 * (6 * tau2 + 6 * e2 - e3_23 + 3 * e23 - 2 * e3 - 6) + 1 / 6 * gamma3 * (-6 * e4 * tau2 + 6 * tau2 + 6 * e2 - 6 * e24 + 6 * e4 - 6))
        a3 = 0
        a4 = 0
        a[1, 1] = summarize_a((a0, a1, a2, a3, a4), r, n0)

        a0 = 1 / 6 * gamma3 * gamma1**2 * (2 * e14 - e3_14) + gamma1 * (1 / 6 * gamma3 * (4 * e1 - 4 * e14) + 1 / 3 * gamma2 * gamma3 * e124 + 1 / 6 * gamma4 * e123) + 1 / 6 * gamma2**2 * gamma3 * (2 * e24 - e3_24) + gamma2 * (1 / 6 * gamma3 * (4 * e2 - 4 * e24) + 1 / 6 * gamma4 * (2 * e23 - e3_23))
        a1 = 1 / 6 * gamma3 * gamma1**2 * (e4 * (e3_1 + 2) - 3 * e14) + 1 / 6 * gamma3 * gamma1 * (-6 * e1 + 6 * e14 - 6 * e4 + 6)
        a2 = 1 / 6 * gamma3 * gamma2**2 * (e3_24 - 3 * e24 + 2 * e4) + gamma2 * (1 / 6 * gamma4 * (e3_23 - 3 * e23 + 2 * e3) - gamma3 * (e2 - e24 + e4 - 1))
        a3 = 0
        a4 = gamma3 * (tau4 + e4 - 1)
        a[1, 2] = summarize_a((a0, a1, a2, a3, a4), r, n0)

        a0 = -1 / 6 * gamma3 * gamma1**2 * e14 + gamma1 * (1 / 3 * gamma3 * e14 + 1 / 6 * gamma2 * gamma3 * (2 * e124 - 4 * e14) + 1 / 6 * gamma4 * (e123 - 2 * e1)) + 1 / 6 * gamma2**2 * gamma3 * (-e3_24 + 6 * e24 - 6 * e4) + 1 / 6 * gamma4 * (6 - 4 * e23) + gamma2 * (1 / 6 * gamma3 * (6 * e4 - 4 * e24) + 1 / 6 * gamma4 * (4 * e2 - e3_23 + 2 * e23 - 6))
        a1 = 0
        a2 = 1 / 6 * gamma3 * gamma2**2 * (-6 * e4 * tau2 + e3_24 - 9 * e24 + 8 * e4) + gamma2 * (1 / 6 * gamma4 * (-6 * tau2 - 6 * e2 + e3_23 - 3 * e23 + 2 * e3 + 6) + 1 / 6 * gamma3 * (6 * (e24 - e4) + 6 * e4 * tau2)) + 1 / 6 * gamma4 * (6 * (e23 - e3) + 6 * tau2)
        a3 = gamma4 * (tau3 + e3 - 1)
        a4 = 0
        a[1, 3] = summarize_a((a0, a1, a2, a3, a4), r, n0)

        a0 = -1 / 6 * gamma3 * gamma1**2 * e14 + gamma1 * (1 / 3 * gamma3 * e14 + 1 / 6 * gamma2 * gamma3 * (2 * e124 - 4 * e14) + 1 / 6 * gamma4 * e123) + 1 / 6 * gamma2**2 * gamma3 * (-e3_24 + 6 * e24 - 6 * e4) + gamma2 * (1 / 6 * gamma3 * (6 * e4 - 4 * e24) + 1 / 6 * gamma4 * (2 * e23 - e3_23))
        a1 = 0
        a2 = 1 / 6 * gamma3 * gamma2**2 * (2 * e4 * (4 - 3 * tau2) + e3_24 - 9 * e24) + gamma2 * (1 / 6 * gamma4 * (e3_23 - 3 * e23 + 2 * e3) + gamma3 * (e4 * (tau2 - 1) + e24))
        a3 = 0
        a4 = 0
        a[1, 4] = summarize_a((a0, a1, a2, a3, a4), r, n0)

        a0 = 1 / 6 * gamma3 * gamma1**2 * (e3_14 - 6 * e14 + 6 * e4) + gamma1 * (1 / 6 * gamma3 * (-4 * e1 + 4 * e14 - 6 * e4 + 6) + 1 / 6 * gamma2 * gamma3 * (4 * e24 - 2 * e124) + 1 / 6 * gamma4 * (2 * e23 - e123)) + 1 / 6 * gamma2**2 * gamma3 * e24 + gamma2 * (1 / 6 * gamma3 * (2 * e2 - 2 * e24) + 1 / 6 * gamma4 * e23)
        a1 = 1 / 6 * gamma3 * gamma1**2 * (6 * e4 * tau1 - e3_14 + 9 * e14 - 8 * e4) + 1 / 6 * gamma3 * gamma1 * (-6 * e4 * tau1 + 6 * tau1 + 6 * e1 - 6 * e14 + 6 * e4 - 6)
        a2 = 0
        a3 = 0
        a4 = 0
        a[2, 2] = summarize_a((a0, a1, a2, a3, a4), r, n0)

        a0 = 1 / 6 * gamma3 * gamma1**2 * (-e3_14 + 6 * e14 - 6 * e4) + gamma1 * (1 / 6 * gamma3 * (6 * e4 - 4 * e14) + 1 / 6 * gamma2 * gamma3 * (2 * e124 - 4 * e24) + 1 / 6 * gamma4 * (e123 - 2 * e23)) - 1 / 6 * gamma2**2 * gamma3 * e24 + 1 / 3 * gamma4 * e23 + gamma2 * (1 / 3 * gamma3 * e24 - 1 / 6 * gamma4 * e23)
        a1 = 1 / 6 * gamma3 * gamma1**2 * e4 * (-6 * tau1 + e3_1 - 9 * e1 + 8) + 1 / 6 * gamma3 * gamma1 * e4 * (6 * (e1 - 1) + 6 * tau1)
        a2 = 0
        a3 = 0
        a4 = 0
        a[2, 3] = summarize_a((a0, a1, a2, a3, a4), r, n0)

        a0 = 1 / 6 * gamma3 * gamma1**2 * (-e3_14 + 6 * e14 - 6 * e4) + gamma1 * (1 / 6 * gamma3 * (6 * e4 - 4 * e14) + 1 / 6 * gamma2 * gamma3 * (2 * e124 - 4 * e24) + 1 / 6 * gamma4 * (-4 * e1 - 2 * e23 + e123 + 6)) - 1 / 6 * gamma2**2 * gamma3 * e24 + gamma2 * (1 / 3 * gamma3 * e24 + 1 / 6 * gamma4 * (2 * e2 - e23))
        a1 = gamma1 * (gamma3 * (e4 * (tau1 - 1) + e14) + gamma4 * (tau1 + e1 - 1)) - 1 / 6 * gamma1**2 * gamma3 * e4 * (6 * tau1 - e3_1 + 9 * e1 - 8)
        a2 = 0
        a3 = 0
        a4 = 0
        a[2, 4] = summarize_a((a0, a1, a2, a3, a4), r, n0)

        a0 = 1 / 2 * gamma3 * gamma1**2 * e14 + gamma1 * (-1 / 3 * gamma3 * e14 + 1 / 6 * gamma2 * gamma3 * (4 * e14 + 4 * e24 - 2 * e124) + 1 / 6 * gamma4 * (2 * e1 + 2 * e23 - e123)) + 1 / 2 * gamma2**2 * gamma3 * e24 - 1 / 3 * gamma4 * e23 + gamma2 * (1 / 6 * gamma4 * (2 * e2 + e23) - 1 / 3 * gamma3 * e24)
        a1 = 0
        a2 = 0
        a3 = 0
        a4 = 0
        a[3, 3] = summarize_a((a0, a1, a2, a3, a4), r, n0)

        a0 = -1 / 2 * gamma3 * gamma1**2 * e14 + gamma1 * (1 / 6 * gamma3 * (2 * e1 + 2 * e14) + 1 / 6 * gamma2 * gamma3 * (-4 * e14 - 4 * e24 + 2 * e124) + 1 / 6 * gamma4 * (e123 - 2 * e23)) - 1 / 2 * gamma2**2 * gamma3 * e24 + 1 / 3 * gamma4 * e23 + gamma2 * (1 / 3 * gamma3 * (e2 + e24) - 1 / 6 * gamma4 * e23)
        a1 = 0
        a2 = 0
        a3 = 0
        a4 = 0
        a[3, 4] = summarize_a((a0, a1, a2, a3, a4), r, n0)

        a0 = 1 / 2 * gamma3 * gamma1**2 * e14 + gamma1 * (-1 / 3 * gamma3 * e14 + 1 / 6 * gamma2 * gamma3 * (4 * e14 + 4 * e24 - 2 * e124) + 1 / 6 * gamma4 * (2 * e23 - e123)) + 1 / 2 * gamma2**2 * gamma3 * e24 + gamma2 * (1 / 6 * gamma4 * e23 - 1 / 3 * gamma3 * e24)
        a1 = 0
        a2 = 0
        a3 = 0
        a4 = 0
        a[4, 4] = summarize_a((a0, a1, a2, a3, a4), r, n0)
        # fmt: on

        return a


class ModelH2(Model):
    def __init__(self, name, mnemo, perms="all"):
        mnemonic_name = "H2:" + mnemo
        super(ModelH2, self).__init__(name, mnemonic_name, perms)

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

        # fmt: off
        a0 = gamma2 * (1 / 6 * gamma3 * (2 * e14 - e124) + 1 / 6 * gamma4 * (-4 * e2 + e3_23 - 2 * e23 + 6)) + gamma1 * (1 / 6 * gamma3 * e14 + 1 / 6 * gamma4 * (2 * e1 - e123))
        a1 = 0
        a2 = 1 / 6 * gamma2 * gamma4 * (6 * tau2 + 6 * e2 - e3_23 + 3 * e23 - 2 * e3 - 6)
        a3 = 0
        a4 = 0
        a[1, 1] = summarize_a((a0, a1, a2, a3, a4), r, n0)

        a0 = gamma1 * (1 / 6 * gamma3 * (2 * e14 - e3_14) + 1 / 6 * gamma4 * e123) + gamma2 * (1 / 6 * gamma3 * e124 + 1 / 6 * gamma4 * (2 * e23 - e3_23))
        a1 = 1 / 6 * gamma1 * gamma3 * e4 * (e3_1 - 3 * e1 + 2)
        a2 = 1 / 6 * gamma2 * gamma4 * e3 * (e3_2 - 3 * e2 + 2)
        a3 = 0
        a4 = 0
        a[1, 2] = summarize_a((a0, a1, a2, a3, a4), r, n0)

        a0 = gamma2 * (1 / 6 * gamma3 * e124 + 1 / 6 * gamma4 * (4 * e2 - e3_23 - 2 * e23)) + gamma1 * (1 / 6 * gamma3 * e14 + 1 / 6 * gamma4 * (-2 * e1 - 4 * e23 + e123 + 6))
        a1 = 0
        a2 = 1 / 6 * gamma2 * gamma4 * (-6 * e2 + e3_23 + 3 * e23 - 4 * e3 + 6) + gamma1 * gamma4 * (tau2 + e23 - e3)
        a3 = gamma1 * gamma4 * (tau3 + e3 - 1) + gamma2 * gamma4 * (tau3 + e3 - 1)
        a4 = 0
        a[1, 3] = summarize_a((a0, a1, a2, a3, a4), r, n0)

        a0 = gamma1 * (1 / 6 * gamma3 * (2 * e1 - e14) + 1 / 6 * gamma4 * e123) + gamma2 * (1 / 6 * gamma3 * (-4 * e2 - 2 * e14 + e124 + 6) + 1 / 6 * gamma4 * (2 * e23 - e3_23))
        a1 = 0
        a2 = gamma2 * (1 / 6 * gamma4 * (e3_23 - 3 * e23 + 2 * e3) + gamma3 * (tau2 + e2 - 1))
        a3 = 0
        a4 = 0
        a[1, 4] = summarize_a((a0, a1, a2, a3, a4), r, n0)

        a0 = gamma2 * (1 / 6 * gamma3 * (2 * e2 - e124) + 1 / 6 * gamma4 * e23) + gamma1 * (1 / 6 * gamma3 * (-4 * e1 + e3_14 - 2 * e14 + 6) + 1 / 6 * gamma4 * (2 * e23 - e123))
        a1 = 1 / 6 * gamma1 * gamma3 * (3 * e1 * (e4 + 2) - e3_14 - 2 * e4 + 6 * tau1 - 6)
        a2 = 0
        a3 = 0
        a4 = 0
        a[2, 2] = summarize_a((a0, a1, a2, a3, a4), r, n0)

        a0 = gamma2 * (1 / 6 * gamma3 * (-2 * e2 - 4 * e14 + e124 + 6) + 1 / 6 * gamma4 * e23) + gamma1 * (1 / 6 * gamma3 * (4 * e1 - e3_14 - 2 * e14) + 1 / 6 * gamma4 * e123)
        a1 = 1 / 6 * gamma1 * gamma3 * (e4 * (e3_1 - 4) + 3 * e1 * (e4 - 2) + 6) + gamma2 * gamma3 * (e4 * (e1 - 1) + tau1)
        a2 = 0
        a3 = 0
        a4 = gamma1 * gamma3 * (tau4 + e4 - 1) + gamma2 * gamma3 * (tau4 + e4 - 1)
        a[2, 3] = summarize_a((a0, a1, a2, a3, a4), r, n0)

        a0 = gamma2 * (1 / 6 * gamma3 * e124 + 1 / 6 * gamma4 * (2 * e2 - e23)) + gamma1 * (1 / 6 * gamma3 * (2 * e14 - e3_14) + 1 / 6 * gamma4 * (-4 * e1 - 2 * e23 + e123 + 6))
        a1 = gamma1 * (1 / 6 * gamma3 * e4 * (e3_1 - 3 * e1 + 2) + gamma4 * (tau1 + e1 - 1))
        a2 = 0
        a3 = 0
        a4 = 0
        a[2, 4] = summarize_a((a0, a1, a2, a3, a4), r, n0)

        a0 = gamma2 * (1 / 6 * gamma3 * (2 * e2 - e124) + 1 / 6 * gamma4 * (2 * e2 - e23)) + gamma1 * (1 / 6 * gamma3 * (2 * e1 - e14) + 1 / 6 * gamma4 * (2 * e1 - e123))
        a1 = 0
        a2 = 0
        a3 = 0
        a4 = 0
        a[3, 3] = summarize_a((a0, a1, a2, a3, a4), r, n0)

        a0 = gamma2 * (1 / 6 * gamma3 * e124 + 1 / 6 * gamma4 * e23) + gamma1 * (1 / 6 * gamma3 * e14 + 1 / 6 * gamma4 * e123)
        a1 = 0
        a2 = 0
        a3 = 0
        a4 = 0
        a[3, 4] = summarize_a((a0, a1, a2, a3, a4), r, n0)

        a0 = gamma2 * (1 / 6 * gamma3 * (2 * e14 - e124) + 1 / 6 * gamma4 * e23) + gamma1 * (1 / 6 * gamma3 * e14 + 1 / 6 * gamma4 * (2 * e23 - e123))
        a1 = 0
        a2 = 0
        a3 = 0
        a4 = 0
        a[4, 4] = summarize_a((a0, a1, a2, a3, a4), r, n0)
        # fmt: on

        return a


# Note: first model in list must be the most complex, last model must be the simplest
# fmt: off
models_H1 = [
    ModelH1("2H1", "TTgg"),
    ModelH1("1H1", "TTg0", [1234, 1243, 1324, 2134, 2143, 2314,
                            3124, 3142, 3214, 4123, 4132, 4213]),
    ModelH1("1H2", "TT1g"),
    ModelH1("1H3", "TT0g", [1234, 1243, 1342, 2134, 2143, 2341,
                            3124, 3142, 3241, 4123, 4132, 4231]),
    ModelH1("1H4", "TTg1", [1234, 1324, 1423, 2314, 2413, 3412]),
    ModelH1("1HP", "T0gg"),
    ModelH1("T1", "TT10", [1234, 1243, 1324, 2134, 2143, 3142]),
    ModelH1("T2", "TT01", [1234, 1324, 1423, 2134, 2314, 2413,
                           3124, 3214, 3412, 4123, 4213, 4312]),
    # ModelH1("1T2A", "TT01"),
    ModelH1("1T2B", "TT11"),
    ModelH1("1HP1", "0Tng", [1234, 1243, 1342, 2134, 2143, 2341,
                             3124, 3142, 3241, 4123, 4132, 4231]),
    ModelH1("1PH1A", "T01g"),
    ModelH1("1HP2", "T0g0", [1234, 1243, 1324, 2134, 2143, 2314,
                             3124, 3142, 3214, 4123, 4132, 4213]),
    ModelH1("1HP3", "T0g1", [1234, 1324, 1423, 2314, 2413, 3412]),
    ModelH1("PT", "0Tn1", [1234, 1324, 1423, 2314, 2413, 3412]),
    ModelH1("TP", "T00n", [1234, 2134, 3124, 4123]),
    # ModelH1("1P2A", "0Tn1"),
    ModelH1("1P2B", "T011"),
    ModelH1("T0", "T010", [1234, 1243, 1324]),
    ModelH1("P", "00nn", [1234]),
]
models_H2 = [
    ModelH2("2H2", "TTgg", [1234, 1243, 1324, 1342, 1423, 1432,
                            2314, 2341, 2413, 2431, 3412, 3421]),
    ModelH2("2HA1", "TTg0"),
    ModelH2("2HA2", "TTg1"),
    ModelH2("2HB1", "TT0g"),
    ModelH2("2HB2", "TT1g"),
    ModelH2("2HP", "T0gg", [1234, 1324, 1423, 2314, 2413, 3412]),
    ModelH2("2T1", "TT10"),
    ModelH2("2T2", "TT00"),
    ModelH2("2T2A", "TT01"),
    ModelH2("2T2B", "TT11"),
    ModelH2("2PH1", "0Tng"),
    ModelH2("2PH2", "T0g0"),
    ModelH2("2PH2A", "T00g"),
    ModelH2("2PH2B", "T01g"),
    ModelH2("2PH2C", "T0g1"),
    ModelH2("2P1", "0Tn0"),
    ModelH2("2P1A", "0Tn1"),
    ModelH2("2P2", "T000"),
    ModelH2("2P2A", "T011"),
    ModelH2("2P3", "T010"),
    ModelH2("2P3A", "T001"),
    ModelH2("PL2", "00nn", [1234]),
]
# fmt: on
all_models = models_H1 + models_H2

models_mapping = Model.mapping
models_mapping_mnemonic = Model.mapping_mnemonic

# fmt: off
models_H1_nr = ["2H1", "1H1", "1H2", "1H3", "1H4", "1HP1", "1HP2",
                "1HP3", "T1", "T2", "PT", "TP", "T0", "P"]
models_H1_nr = [models_mapping[name] for name in models_H1_nr]
models_H2_nr = ["2H2", "2HP"]
models_H2_nr = [models_mapping[name] for name in models_H2_nr]
# fmt: on

models_nrds = {
    "N0": ["P"],
    "N1": ["PT", "TP"],
    "N2": ["1HP1", "1HP2", "1HP3", "T1", "T2"],
    "N3": ["1H1", "1H2", "1H3", "1H4", "2HP"],
    "N4": ["2H1", "2H2"],
}
models_nrds["NR"] = [
    name for i in range(0, 4 + 1) for name in models_nrds["N{}".format(i)]
]
models_nrds = {
    level: [models_mapping[name] for name in names]
    for level, names in models_nrds.items()
}

models_hierarchy = {
    "H1": {
        "free": [
            ("2H1", "1H1 1H2 1H3 1H4 1HP"),
            ("1H1", "T1 T2 1HP1 1HP2 1HP3"),
            ("1H2", "T1 T2 1HP1 1HP2 1HP3"),
            ("1H3", "T1 T2 1HP1 1HP2 1HP3"),
            ("1H4", "T1 T2 1HP1 1HP2 1HP3"),
            ("1HP", "T1 T2 1HP1 1HP2 1HP3"),
            ("T1", "PT PT T0"),
            ("T2", "PT PT T0"),
            ("1HP1", "PT PT T0"),
            ("1HP2", "PT PT T0"),
            ("1HP3", "PT PT T0"),
            ("PT", "P"),
            ("PT", "P"),
            ("T0", "P"),
        ],
        "fixed": [
            ("2H1", "1H1 1H2 1H3 1H4 1HP 1HP1"),
            ("1H1", "T1 T2 PT 1HP2"),
            ("1H2", "1HP1 1T2B T1 1PH1A"),
            ("1H3", "1T2A T2 1HP1 PT"),
            ("1H4", "1T2B 1T2A 1HP3 1P2A"),
            ("1HP", "P PT 1HP2 1HP3 1PH1A"),
            ("T1", "PT T0"),
            ("T2", "PT PT"),
            ("1T2A", "PT 1P2A"),
            ("1T2B", "1P2A 1P2B"),
            ("1HP1", "1P2A P"),
            ("1PH1A", "1P2B T0 P"),
            ("1HP2", "PT T0 P"),
            ("1HP3", "PT 1P2B P"),
            ("PT", "P"),
            ("PT", "P"),
            ("1P2A", "P"),
            ("1P2B", "P"),
            ("T0", "P"),
        ],
    },
    "H2": {
        "free": [
            ("2H2", "2HA1 2HB1 2HP"),
            ("2HA1", "2T1 2T2 2PH1 2PH2"),
            ("2HB1", "2T1 2T2 2PH1 2PH2"),
            ("2HP", "2T1 2T2 2PH1 2PH2"),
            ("2T1", "2P1 2P2 2P3"),
            ("2T2", "2P1 2P2 2P3"),
            ("2PH1", "2P1 2P2 2P3"),
            ("2PH2", "2P1 2P2 2P3"),
            ("2P1", "PL2"),
            ("2P2", "PL2"),
            ("2P3", "PL2"),
        ],
        "fixed": [
            ("2H2", "2HA1 2HA2 2HB1 2HB2 2HP"),
            ("2HA1", "2PH2 2T2 2T1"),
            ("2HA2", "2P1A 2T2B 2T2A 2PH2C"),
            ("2HB1", "2T2A 2PH1 2PH2B 2PH2A"),
            ("2HB2", "2T1 2T2B 2PH1 2PH2B"),
            ("2HP", "2PH2 2PH2A 2PH2B 2PH2C PL2"),
            ("2T1", "2P3 2P1"),
            ("2T2", "2P1 2P2"),
            ("2T2A", "2P1A 2P3A"),
            ("2T2B", "2P1A 2P2A"),
            ("2PH1", "2P1 2P1A PL2"),
            ("2PH2", "2P2 2P3 PL2"),
            ("2PH2A", "2P2 2P3A PL2"),
            ("2PH2B", "2P1 2P3"),
            ("2PH2C", "2P2A 2P3A"),
            ("2P1", "PL2"),
            ("2P1A", "PL2"),
            ("2P2", "PL2"),
            ("2P2A", "PL2"),
            ("2P3", "PL2"),
            ("2P3A", "PL2"),
        ],
    },
}
models_hierarchy = {
    group: {
        freeness: OrderedDict(
            [(parent, children.split()) for parent, children in hierarchy]
        )
        for freeness, hierarchy in group_hierarchy.items()
    }
    for group, group_hierarchy in models_hierarchy.items()
}
