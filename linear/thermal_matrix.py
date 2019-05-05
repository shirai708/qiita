import copy

import matplotlib
import matplotlib.pyplot as plt
from scipy import linalg
import numpy as np

plt.switch_backend("Agg")

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

plt.savefig("result_matrix.png")

# 最大固有値と対応する固有ベクトル
w, v = linalg.eigh(A, eigvals=(N-1,N-1))
print(v)
