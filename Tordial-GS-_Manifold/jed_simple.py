cat > jed_simple.py << 'PYEOF'
import plotext as plt

cycles = list(range(1, 19))
delta_e = [2.537, 2.066, 1.629, 1.214, 0.818, 0.435, 0.052, -0.332, -0.726, -1.136, -1.568, -2.033, -2.488, -2.534, -2.534, -2.534, -2.534, -2.534]
spin    = [0.820, 0.931, 1.057, 1.200, 1.362, 1.546, 1.755, 1.992, 2.261, 2.566, 2.912, 3.305, 3.751, 3.800, 3.800, 3.800, 3.800, 3.800]

plt.clf()
plt.plot(cycles, delta_e, label="ΔE", color="red")
plt.plot(cycles, spin, label="Spin", color="cyan")
plt.title("JED Run — ΔE (red) & Spin (cyan)")
plt.xlabel("Cycle")
plt.ylabel("Value")
plt.show()
PYEOF

python jed_simple.py