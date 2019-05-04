import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import numpy as np
import copy


def calc(v, v2, h):
    N = len(v)
    for i in range(N):
        i1 = (i+1) % N
        i2 = (i - 1 + N) % N
        v2[i] = v[i] + (v[i1] - 2.0*v[i] + v[i2])*h


N = 32
v = np.array([min(x,N-x) for x in range(N)],dtype='float64')
v2 = np.zeros(N)

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
    plt.plot(s)

plt.savefig("test.png")
