__all__ = ('Optimizer', )

from collections import OrderedDict

from scipy.optimize import minimize

from .utils import morph4, morph10, likelihood
from .printers import log_debug


class Optimizer:

    def __init__(self, species, ys, theta0, r, method, debug=False, **kwargs):
        self.species = species
        self.ys = ys
        self.theta0 = theta0
        self.r = r
        self.method = method
        self.debug = debug
        self.options = {'maxiter': 500, **kwargs}

    def one(self, model, perm):
        if self.debug:
            log_debug('Optimizing model {} for permutation [{}]...'
                      .format(model, ', '.join(morph4(self.species, perm))))
        return minimize(lambda theta: -likelihood(model, morph10(self.ys, perm), theta, self.r),
                        self.theta0, bounds=model.bounds, method=self.method, options=self.options)

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
