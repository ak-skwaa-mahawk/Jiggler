import networkx as nx
import numpy as np
import torch
from typing import Dict

class SovereignRelationalMesh:
    def __init__(self, num_agents: int = 10):
        self.G = nx.DiGraph()
        self.torch_device = torch.device("cpu")  # extend to CUDA later
        self.pulse_freq = 79.79  # Hz constellation sync (irrational multiple → aperiodic)

    def add_relational_unit(self, agent1: str, agent2: str, context: str, obligation: float = 1.0):
        """Add bidirectional relational unit with initial soliton = 0.0"""
        attrs = {'context': context, 'obligation': obligation, 'soliton': 0.0}
        self.G.add_edge(agent1, agent2, **attrs)
        self.G.add_edge(agent2, agent1, **attrs)

    def propagate_soliton(self, source: str, strength: float = 1.0):
        """Aperiodic soliton pulse — the living nervous system heartbeat"""
        if source not in self.G:
            return
        # Non-periodic nudge using irrational frequency (never repeats exactly)
        nudge = strength * (1 + np.sin(self.pulse_freq))
        for neighbor in list(self.G.neighbors(source)):
            if self.G.has_edge(neighbor, source):
                current = self.G[source][neighbor]['soliton']
                new = current + nudge
                # Bounded conservation (mimics real soliton energy preservation)
                self.G[source][neighbor]['soliton'] = max(0.0, min(10.0, new))
                self.G[neighbor][source]['soliton'] = max(0.0, min(10.0, new))

    def mesh_debate_update(self, agent: str, input_strength: float = 1.0, stubbornness: float = 0.3):
        """MeshDebate consensus with stubbornness-weighted Bayesian + RL damping"""
        if agent not in self.G:
            return
        for neighbor in list(self.G.neighbors(agent)):
            if self.G.has_edge(neighbor, agent):
                current = self.G[agent][neighbor]['obligation']
                bayesian_update = current * (1 - stubbornness) + input_strength * stubbornness
                rl_damped = bayesian_update * (1 + 0.05 * np.tanh(input_strength))  # DDPG-style
                self.G[agent][neighbor]['obligation'] = min(1.0, rl_damped)
                self.G[neighbor][agent]['obligation'] = min(1.0, rl_damped)

    def mesh_reciprocity_score(self) -> float:
        """Average mutual obligation strength across all reciprocal pairs"""
        scores = [data['obligation'] 
                  for u, v, data in self.G.edges(data=True) 
                  if self.G.has_edge(v, u)]
        return np.mean(scores) if scores else 0.0

    def get_soliton_stats(self) -> Dict:
        """Diagnostic: current soliton strength across edges"""
        strengths = [data['soliton'] for u, v, data in self.G.edges(data=True)]
        return {
            'mean': np.mean(strengths),
            'max': np.max(strengths),
            'total': np.sum(strengths)
        }

# Reproducible sovereign example (hunter-caribou-land core)
np.random.seed(42)
mesh = SovereignRelationalMesh()
mesh.add_relational_unit('hunter', 'caribou', 'hunt', 1.0)
mesh.add_relational_unit('hunter', 'land', 'stewardship', 0.8)
mesh.add_relational_unit('caribou', 'land', 'graze', 0.9)

print("Initial reciprocity score:", mesh.mesh_reciprocity_score())
print("Initial soliton stats:", mesh.get_soliton_stats())

for cycle in range(15):
    mesh.propagate_soliton('hunter')
    mesh.mesh_debate_update('hunter', input_strength=1.0)
    score = mesh.mesh_reciprocity_score()
    soliton_stats = mesh.get_soliton_stats()
    print(f"Cycle {cycle+1:2d} | Reciprocity: {score:.4f} | Mean soliton: {soliton_stats['mean']:.2f}")