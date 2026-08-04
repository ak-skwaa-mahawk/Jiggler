from tordial_gs_py import TordialClusterPy
import numpy as np

N = 64
cluster = TordialClusterPy(8, N, N, 2.0, 0.5)

θ = np.linspace(0, 2*np.pi, N, endpoint=False)
φ = np.linspace(0, 2*np.pi, N, endpoint=False)
Θ, Φ = np.meshgrid(θ, φ, indexing="ij")

Φ0 = np.zeros((N, N))
ρGS = 1 + 0.2*np.cos(Θ)*np.cos(Φ)
κ = 0.5*np.ones_like(ρGS)

cluster.set_fields_all(Φ0, ρGS, κ)

for _ in range(200):
    cluster.step_all(1.0, 1.0, 1.0, 0.01, 0.0)
    cluster.sync_low_modes(4)

Φ_node0 = cluster.get_phi(0)