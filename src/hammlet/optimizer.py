import itertools
from collections import namedtuple
from operator import attrgetter

from scipy.optimize import minimize

from .models import constraint_value, models_H1_nr, models_H2_nr
from .printers import log_debug
from .utils import convert_permutation, likelihood, morph10

__all__ = ["Optimizer"]

OptimizationResult = namedtuple("OptimizationResult", "model permutation LL theta")


class Optimizer:
    """Maximum Likelihood Estimator."""

    def __init__(self, y, r, theta0, method, debug=False, **kwargs):
        self.y = y
        self.r = r
        self.theta0 = theta0
        self.method = method
        self.debug = debug
        self.options = {"maxiter": 500}
        self.options.update(kwargs)

    def one(self, model, perm):
        if self.debug:
            log_debug(
                "Optimizing model {} for permutation {}...".format(
                    model, "".join(map(str, perm))
                )
            )
        bounds = model.get_safe_bounds()
        theta0 = tuple(
            constraint_value(param, bound) for param, bound in zip(self.theta0, bounds)
        )
        # maximize `likelihood`  ==  minimize `-likelihood`
        result = minimize(
            lambda theta: -likelihood(model, morph10(self.y, perm), theta, self.r),
            theta0,
            bounds=bounds,
            method=self.method,
            options=self.options,
        )
        LL = float(-result.fun)
        theta = tuple(result.x)
        return OptimizationResult(model, perm, LL, theta)

    def many(self, models, perms="all", sort=True):
        results = []

        for model in models:
            if perms == "model":
                ps = model.perms
            elif perms == "model_nr":
                if model in models_H1_nr:
                    ps = "all"
                elif model in models_H2_nr:
                    ps = "half"
                else:
                    raise ValueError(
                        "Bad model '{}' for model_nr perms mode".format(model)
                    )
            else:
                ps = perms

            if ps == "all":
                ps = list(itertools.permutations((1, 2, 3, 4)))
            elif ps == "half":
                ps = list(itertools.permutations((1, 2, 3, 4)))[:12]
            else:
                ps = list(map(convert_permutation, ps))

            for perm in ps:
                results.append(self.one(model, perm))

        if sort:
            results.sort(key=attrgetter("LL"), reverse=True)

        return results

    def many_perms(self, model, perms, sort=True):
        return self.many([model], perms, sort=sort)

    def many_models(self, models, perm, sort=True):
        return self.many(models, [perm], sort=sort)
