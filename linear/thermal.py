import copy

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

plt.switch_backend("Agg")


def calc(v, h):
    v2 = copy.copy(v)
    N = len(v)
    for i in range(N):
        i1 = (i+1) % N
        i2 = (i - 1 + N) % N
        v[i] = v2[i] + (v2[i1] - 2.0*v2[i] + v2[i2])*h


N = 32
v = np.array([min(x, N-x) for x in range(N)], dtype='float64')

h = 0.1
r = []
for i in range(1000):
    calc(v, h)
    if (i % 100) == 0:
        r.append(copy.copy(v))

for s in r:
    plt.plot(s)

plt.savefig("result.png")
