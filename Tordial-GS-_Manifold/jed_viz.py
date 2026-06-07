import plotext as plt
import numpy as np

cycles = list(range(1, 19))
delta_e = [2.537, 2.066, 1.629, 1.214, 0.818, 0.435, 0.052, -0.332, -0.726, -1.136, -1.568, -2.033, -2.488, -2.534, -2.534, -2.534, -2.534, -2.534]
spin    = [0.820, 0.931, 1.057, 1.200, 1.362, 1.546, 1.755, 1.992, 2.261, 2.566, 2.912, 3.305, 3.751, 3.800, 3.800, 3.800, 3.800, 3.800]
temp    = [0.880, 0.766, 0.666, 0.579, 0.504, 0.438, 0.381, 0.331, 0.288, 0.251, 0.218, 0.190, 0.180, 0.180, 0.180, 0.180, 0.180, 0.180]
throat  = [56.17, 52.20, 48.38, 44.72, 41.30, 38.06, 35.01, 32.19, 29.56, 27.10, 24.85, 22.75, 20.78, 21.24, 21.86, 21.86, 21.86, 21.86]
belt    = [56.30, 58.26, 60.28, 62.36, 64.57, 66.83, 69.16, 71.60, 74.11, 76.68, 79.38, 82.13, 85.01, 88.01, 90.58, 90.58, 90.58, 90.58]
task    = [0.350, 0.438, 0.429, 0.415, 0.396, 0.372, 0.343, 0.310, 0.351, 0.400, 0.456, 0.521, 0.597, 0.683, 0.692, 0.692, 0.692, 0.692]
coh     = [0.896, 0.676, 0.700, 0.735, 0.782, 0.841, 0.914, 0.998, 0.894, 0.772, 0.631, 0.468, 0.280, 0.065, 0.041, 0.041, 0.041, 0.041]
relax   = [0.62, 0.69, 0.76, 0.82, 0.88, 0.93, 0.99, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00, 1.00]

plt.clf()
plt.subplots(2, 2)

# Panel 1: Energy & Spin
plt.subplot(1, 1)
plt.plot(cycles, delta_e, label="ΔE", color="red")
plt.plot(cycles, spin, label="Spin", color="cyan")
plt.title("Semantic Arc — ΔE & Spin")
plt.xlabel("Cycle")
plt.ylabel("Value")

# Panel 2: Temperature
plt.subplot(1, 2)
plt.plot(cycles, temp, label="Temp", color="orange")
plt.title("Cooling Trajectory")
plt.xlabel("Cycle")

# Panel 3: Throat / Belt duality
plt.subplot(2, 1)
plt.plot(cycles, throat, label="Throat", color="magenta")
plt.plot(cycles, belt, label="Belt", color="green")
plt.title("Physics Arc — Throat Contraction / Belt Expansion")
plt.xlabel("Cycle")

# Panel 4: Coherence, Task, Relax
plt.subplot(2, 2)
plt.plot(cycles, coh, label="Coherence", color="blue")
plt.plot(cycles, task, label="Task", color="yellow")
plt.plot(cycles, relax, label="Relax", color="white")
plt.title("Cognitive Arc — Lock Formation")
plt.xlabel("Cycle")

plt.show()