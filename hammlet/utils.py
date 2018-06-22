__all__ = ('morph4', 'morph10', 'ij2pattern', 'pattern2ij', 'get_a', 'likelihood')

import numpy as np


def morph4(iterable, permutation):
    """Apply permutation on 4-iterable.

    >>> morph4('ABCD', None)
    'ABCD'
    >>> morph4('ABCD', (0, 1, 2, 3))
    'ABCD'
    >>> morph4('ABCD', (1, 3, 2, 0))
    'BDCA'
    >>> morph4(('A', 'B', 'C', 'D'), (1, 3, 2, 0))
    ('B', 'D', 'C', 'A')
    """
    if permutation is None:
        return iterable
    if isinstance(iterable, str):
        return ''.join(iterable[i] for i in permutation)
    elif isinstance(iterable, list):
        return list(iterable[i] for i in permutation)
    elif isinstance(iterable, tuple):
        return tuple(iterable[i] for i in permutation)
    # elif isinstance(iterable, dict):
    #     return {morph(key, permutation): value for key, value in iterable.items()}
    else:
        raise NotImplementedError('iterable type <{}> is not supported'.format(type(iterable)))


def morph10(iterable, permutation):
    """Apply permutation on 10-iterable. (y-values)

    >>> morph10(42, None)
    42
    >>> morph10((1, 2, 3, 4, 5, 6, 7, 8, 9, 10), (1, 3, 2, 0))
    (5, 7, 6, 2, 10, 9, 4, 8, 3, 1)
    """
    if permutation is None:
        return iterable
    A = {}
    it = iter(iterable)
    for i in range(4):
        for j in range(i, 4):
            A[i, j] = A[j, i] = next(it)

    return tuple(A[permutation[i], permutation[j]] for i in range(4) for j in range(i, 4))


def ij2pattern(i, j):
    """Convert (i,j) pair into string pattern.

    >>> ij2pattern(1, 1)
    '-+++'
    >>> ij2pattern(2, 3)
    '+--+'
    >>> ij2pattern(1, 4)
    '-++-'
    >>> ij2pattern(4, 4)
    '+++-'
    """
    return ''.join('-' if t + 1 in (i, j) else '+' for t in range(4))


def pattern2ij(pattern):
    """Convert string pattern into (i,j) pair.

    >>> pattern2ij('-+++')
    (1, 1)
    >>> pattern2ij('+--+')
    (2, 3)
    >>> pattern2ij('-++-')
    (1, 4)
    >>> pattern2ij('+++-')
    (4, 4)
    """
    return (pattern.find('-') + 1, pattern.rfind('-') + 1)


def get_a(model, theta, r):
    """Return `a` values from model.

    >>> from hammlet.models import models_mapping
    >>> a = get_a(models_mapping['2H1'], (100,1,2,0.6,0.3), (1,1,1,1))
    >>> [round(x, 3) for x in a]
    [49.819, 58.596, 177.022, 2.444, 21.024, 1.816, 51.238, 8.548, 3.715, 1.126]
    """
    return tuple(a_ij for _, a_ij in sorted(model(theta, r).items()))


def poisson(a, y):
    """Log-poisson.

    >>> poisson(10, 30).round(5)
    59.07755
    >>> poisson([3, 14], [15, 9]).round(5)
    array([13.47918,  9.75152])
    """
    return y * np.log(a) - a


def likelihood(model, ys_, theta, r):
    """Log-likelihood.

    L(theta | y) = sum_{i,j} y_ij * ln( a_ij(theta) ) - a_ij(theta)

    >>> from hammlet.models import models_mapping
    >>> likelihood(models_mapping['2H1'], (9,9,100,9,9,9,9,9,9,9), (100,1,2,.6,.3), (1,1,1,1)).round(5)
    322.53058
    """
    # ys_ is morphed
    # Note: do not morph `a`!!!
    a = get_a(model, theta, r)
    return poisson(a, ys_).sum()
