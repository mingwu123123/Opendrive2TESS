import collections
import json
from functools import lru_cache

import matplotlib.pyplot as plt

from math import sin
from cmath import cos, pi
from matlab import zeros, linspace
size = 3

mapping = {
    'x': collections.defaultdict(dict),
    'y': collections.defaultdict(dict)
}

@lru_cache(maxsize=10000)
def get_integrate_basic(lower, higher, type):
    from sympy import Symbol, integrate, sqrt, cos, pi, sin
    t = Symbol("t")
    c1 = (1 / sqrt(2 * pi)) * (cos(t) / sqrt(t))
    s1 = (1 / sqrt(2 * pi)) * (sin(t) / sqrt(t))
    if type == "x":
        a = integrate(c1, (t, lower, higher))
    elif type == 'y':
        a = integrate(s1, (t, lower, higher))
    return a


# 在此处将角度统一化
def get_integrate(lower, higher, type):
    lower = round(lower, size)
    higher = round(higher, size)
    lower = min(pi, max(lower, -pi))
    higher = min(pi, max(higher, -pi))
    print(lower, higher, type)

    mapping[type]['%.4f' % lower]['%.4f' % higher] = float(get_integrate_basic(lower, higher, type))



for i in linspace(-pi, pi, int(pi*2//(0.1 ** size))):
    get_integrate(0, i, 'x')
    get_integrate(0, i, 'y')
with open(f'files/integrate_{size}.json', 'w') as f:
    json.dump(mapping, f)
