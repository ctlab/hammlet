from collections import namedtuple
from operator import attrgetter

from scipy.optimize import minimize

from .printers import log_debug
from .utils import likelihood, morph10

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
                "Optimizing model {} for permutation ({})...".format(
                    model, ",".join(map(str, perm))
                )
            )
        # maximize `likelihood`  ==  minimize `-likelihood`
        result = minimize(
            lambda theta: -likelihood(model, morph10(self.y, perm), theta, self.r),
            self.theta0,
            bounds=model.get_safe_bounds(),
            method=self.method,
            options=self.options,
        )
        LL = float(-result.fun)
        theta = tuple(result.x)
        return OptimizationResult(model, perm, LL, theta)

    def many(self, models, perms, sort=True):
        results = [self.one(model, perm) for model in models for perm in perms]
        if sort:
            results.sort(key=attrgetter("LL"), reverse=True)
        return results

    def many_perms(self, model, perms, sort=True):
        return self.many([model], perms, sort=sort)

    def many_models(self, models, perm, sort=True):
        return self.many(models, [perm], sort=sort)
