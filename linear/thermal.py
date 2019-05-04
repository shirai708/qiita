from matplotlib import pyplot
import numpy as np
import copy

N = 32


def calc(v, v2, h):
    for i in range(N):
        i1 = (i+1) % N
        i2 = (i - 1 + N) % N
        v2[i] = v[i] + (v[i1] - 2.0*v[i] + v[i2])*h


N = 32
v = np.zeros(N)
v2 = np.zeros(N)
for i in range(N):
    if i < N/2:
        v[i] = i
    else:
        v[i] = N - i
h = 0.1
r = []
for i in range(1000):
    if (i % 2) == 0:
        calc(v, v2, h)
    else:
        calc(v2, v, h)
    if (i % 100) == 0:
        r.append(copy.copy(v))
for s in r:
    pyplot.plot(s)
