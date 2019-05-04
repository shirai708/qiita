import copy

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np



N = 32
v = np.array([min(x, N-x) for x in range(N)], dtype='float64')
A = np.zeros((N, N))

h = 0.1
for i in range(N):
    i1 = (i + 1) % N
    i2 = (i - 1 + N) % N
    A[i][i] = 1.0 - 2.0*h
    A[i][i1] = h
    A[i][i2] = h

r = []
for i in range(1000):
    v = A.dot(v)
    if (i % 100) == 0:
        r.append(copy.copy(v))

for s in r:
    plt.plot(s)

plt.savefig("test2.png")
