import matplotlib.pyplot as plt

vq = []
vp = []
h = 0.05

q = 1.0
p = 0.0
for i in range(1000):
    (tp, tq) = (p, q)
    (p, q) = (tp - h * tq, tq + h * tp)
    vp.append(p)
    vq.append(q)

plt.plot(vq, vp)

plt.savefig("euler.png")
