__all__ = ('Instance', )

import time
from itertools import permutations
from collections import OrderedDict

from .printers import *
from .utils import *


class Instance:

    def __init__(self, species, ys, models, theta0, r, method, parallel,
                 compact, no_polytomy, number_of_best, debug):
        self.species = species
        self.ys = ys
        self.models = models
        self.theta0 = theta0
        self.r = r
        self.method = method
        self.parallel = parallel
        self.compact = compact
        self.no_polytomy = no_polytomy
        self.number_of_best = number_of_best
        self.debug = debug

    def only_show_permutation(self, show_permutation):
        # TODO: todo
        perm = tuple(self.species.index(s) for s in show_permutation)
        ys_ = morph10(self.ys, perm)
        log_info('{}, {}'.format(', '.join(show_permutation),
                                 ', '.join(map(str, ys_))),
                 symbol='@')

    def run_only_a(self, only_permutation=None):
        log_info('Doing only a_ij calculations...')
        time_start = time.time()

        if only_permutation:
            perm = tuple(self.species.index(s) for s in only_permutation)
        else:
            perm = None

        for model in self.models:
            a = get_a(model, self.theta0, self.r)

            log_success('Result for permutation [{}], model {}, theta = {}, r = {}:'
                        .format(', '.join(morph4(self.species, perm)), model, self.theta0, self.r))
            print_a(a, self.ys, perm)

            if self.debug:
                from .utils import likelihood
                log_debug('LL = {:.2f}'.format(likelihood(model_func, morph10(self.ys, perm), self.theta0, self.r)))

                options = {'maxiter': 500}
                worker = Worker(model_func, self.ys, self.theta0, model.bounds, self.r, self.method, options)
                _, result = worker(perm)
                log_debug(result, symbol=None)

        log_success('Done in {:.1f} s.'.format(time.time() - time_start))

    def run(self, only_permutation=None):
        log_info('Doing calculations for {} model{} ({}) using optimization method {}...'
                 .format(len(self.models),
                         's' if len(self.models) > 1 else '',
                         ','.join(map(str, self.models)),
                         self.method))

        if only_permutation:
            perms = [tuple(self.species.index(s) for s in only_permutation)]
        else:
            perms = list(permutations(range(len(self.species))))

        for model in self.models:
            self.run_model(model, perms)

    def run_model(self, model, perms):
        time_start_optimize = time.time()
        log_br()
        log_info('Optimizing model {}...'.format(model))

        options = {'maxiter': 500}

        results = OrderedDict()  # {permutation: result}

        worker = Worker(model, self.ys, self.theta0, model.bounds, self.r, self.method, options)
        if self.parallel > 1:
            from multiprocessing import Pool
            pool = Pool(self.parallel, Worker.ignore_sigint)
            it = pool.imap(worker, perms)
            pool.close()
        else:
            it = map(worker, perms)

        for perm, result in it:
            results[perm] = result
            if self.debug:
                log_debug('Permutation [{}] done after {} iterations'
                          .format(', '.join(morph4(self.species, perm)), result.nit))
            if not result.success:
                log_error('Optimization for model {} failed on permutation [{}] with message: {}'
                          .format(model, ', '.join(morph4(self.species, perm)), result.message))
                if self.debug:
                    log_debug('result:\n{}'.format(result))

                another_method = {'L-BFGS-B': 'SLSQP', 'SLSQP': 'L-BFGS-B'}[self.method]
                log_info('Retrying optimize permutation [{}] with another method ({})...'
                         .format(', '.join(morph4(self.species, perm)), another_method))
                worker.method = another_method
                _, result = worker(perm)

                if self.debug:
                    log_debug('Permutation [{}] done after {} iterations'
                              .format(', '.join(morph4(self.species, perm)), result.nit))
                if result.success:
                    results[perm] = result
                else:
                    log_error('Optimization retry for model {} failed on permutation [{}] with message: {}'
                              .format(model, ', '.join(morph4(self.species, perm)), result.message))
                    if self.debug:
                        log_debug('result:\n{}'.format(result))

        # assert all(result.success for result in results.values()), "Something gone wrong"

        tmp = sorted(results.items(), key=lambda t: t[1].fun)[:self.number_of_best]
        if tmp:
            if not self.compact:
                log_info('Hybridization model {} results:'.format(model))
            for i, (perm, result) in enumerate(tmp, start=1):
                fit = -result.fun
                theta = result.x

                # Do not print polytomy (all parameters except n0 are zero)
                if self.no_polytomy and all(abs(x) < 1e-3 for x in theta[1:]):
                    continue

                if self.compact:
                    print_compact(i, model, morph4(self.species, perm), fit, theta)
                else:
                    a = get_a(model_func, theta, self.r)
                    print_best(i, morph4(self.species, perm), fit, theta)
                    print_a(a, self.ys, perm)

        if self.parallel > 1:
            pool.join()

        log_success('Done optimizing model {} in {:.1f} s.'.format(model, time.time() - time_start_optimize))
