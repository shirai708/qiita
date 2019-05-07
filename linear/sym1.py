import matplotlib.pyplot as plt

vq = []
vp = []
h = 0.05

q = 1.0
p = 0.0
for i in range(1000):
    p = p - h * q
    q = q + h * p
    vp.append(p)
    vq.append(q)

plt.plot(vq, vp)

plt.savefig("sym1.png")
