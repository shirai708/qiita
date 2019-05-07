import matplotlib.pyplot as plt
import numpy as np
from scipy import linalg

N = 32
A = np.zeros((N, N))
d = 3.0
V = np.array([-d if i in range(N//4, 3*N//4) else 0 for i in range(N)])
for i in range(N):
    i1 = (i + 1) % N
    i2 = (i - 1 + N) % N
    A[i][i] = 2.0 + V[i]
    A[i][i1] = -1
    A[i][i2] = -1
w, v = linalg.eigh(A)
v = v.transpose()
i0 = np.argmax(abs(w))
v0 = np.power(v, 2)[i0]
plt.plot(v0*20+w[i0])
print(w[i0])
plt.plot(V)
plt.savefig("eigen2.png")


vr = v[i0]
plt.cla()
plt.plot(vr)
plt.savefig("eigen2_raw.png")


i0 = np.argmin(w)
plt.cla()
v0 = np.power(v, 2)[i0]
plt.plot(v0*20+w[i0])
print(w[i0])
plt.plot(V)
plt.savefig("eigen3.png")
