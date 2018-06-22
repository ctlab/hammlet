__all__ = ('Instance', )

from collections import OrderedDict

from scipy.optimize import minimize

from .printers import *
from .utils import *


class Instance:

    '''Model Optimization Task'''

    def __init__(self, species, ys, model, theta0, r, method, debug=False):
        self.species = species
        self.ys = ys
        self.model = model
        self.theta0 = theta0
        self.r = r
        self.method = method
        self.debug = debug

    def optimize_one(self, perm):
        if self.debug:
            log_debug('Optimizing model {} for permutation [{}]...'
                      .format(self.model, ', '.join(morph4(self.species, perm))))

        options = {'maxiter': 500}
        result = minimize(lambda theta: -likelihood(self.model, morph10(self.ys, perm), theta, self.r),
                          self.theta0, bounds=self.model.bounds, method=self.method, options=options)

        return result

    def optimize_all(self, perms):
        results = OrderedDict()
        for perm in perms:
            results[perm] = self.optimize_one(perm)
        return results
