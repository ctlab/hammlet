from collections import OrderedDict, namedtuple

from scipy.optimize import minimize

from .printers import log_debug
from .utils import likelihood, morph10

__all__ = ['Optimizer']

OptimizationResult = namedtuple('OptimizationResult', 'model permutation LL theta')


class Optimizer:

    def __init__(self, y, r, theta0, method, debug=False, **kwargs):
        self.y = y
        self.r = r
        self.theta0 = theta0
        self.method = method
        self.debug = debug
        self.options = {'maxiter': 500}
        self.options.update(kwargs)

    def one(self, model, perm):
        if self.debug:
            log_debug('Optimizing model {} for permutation ({})...'
                      .format(model, ','.join(map(str, perm))))
        # maximize `likelihood`  ==  minimize `-likelihood`
        result = minimize(lambda theta: -likelihood(model, morph10(self.y, perm), theta, self.r),
                          self.theta0, bounds=model.get_safe_bounds(), method=self.method, options=self.options)
        LL = float(-result.fun)
        theta = tuple(result.x)
        return OptimizationResult(model, perm, LL, theta)

    def many_perms(self, model, perms):
        results = OrderedDict()  # {perm: result} for model
        for perm in perms:
            results[perm] = self.one(model, perm)
        return results

    def many_models(self, models, perm):
        results = OrderedDict()  # {model_name: result} for perms
        for model in models:
            results[model.name] = self.one(model, perm)
        return results

    def many_many(self, models, perms):
        return [self.one(model, perm)
                for model in models
                for perm in perms]
