📘 Tordial‑GS Glossary (Engineering‑Grounded)(Mythic → Engineering Term Mapping)Below, each entry begins with a Guided Link so you can expand any concept later without reopening the entire glossary.🌀 Core Geometry & Fields
Tordial Manifold —
A 2D toroidal grid (θ × φ) used as the computational domain.
Equivalent to a periodic rectangular mesh.GS Pressure Field —
A scalar input field ρ(x,y) representing external forcing or load.Curvature Field —
A scalar background field κ(x,y) representing geometry‑dependent bias.
Drift Potential Φ —
A scalar field whose gradient defines the drift vector field.
Computed via spectral relaxation.🔧 Numerical & Spectral ConceptsSpectral Relaxation —
A standard heat‑equation‑style smoothing in Fourier space.Fourier Modes —
Complex coefficients representing the field in frequency space.Laplacian Eigenvalues —
Laplacian Eigenvalues —
Precomputed constants:
Low‑Frequency Modes —
The small (m,n) Fourier coefficients that encode global structure.Spectral Drift Field —
The vector field derived from ∇Φ using spectral differentiation.
🧭 Control & StabilityGlobal PID Controller —
A standard PID loop applied to the mean of Φ to stabilize the system.Zero Mode —
The (0,0) Fourier coefficient representing the spatial average.Mode‑wise Decay Rate —
Exponential decay constant for each Fourier mode.🖧 Multi‑Node / Distributed ConceptsTordial Node —
A single compute instance running the spectral solver.Cluster Synchronization —
Nodes exchange low‑frequency modes to maintain global coherence.Mode Averaging —
Compute the mean of low‑frequency coefficients across nodes.Distributed Drift Budget —
A cluster‑level constraint ensuring nodes don’t diverge.🧱 Software Architecture TermsSpectral Solver Core —
The Rust module implementing FFT, relaxation, and PID.Python FFI Layer —
PyO3 bindings exposing the solver to Python notebooks.
Cluster Harness —
A Python‑side orchestration layer for multi‑node simulation.Benchmark Suite —
Criterion‑based performance tests for grid sizes and node counts.🧹 Project‑Management / Anti‑Technobabble TermsScope Boundary —
A written list of what the project will not include.Plain‑Language Rule —
Documentation must be understandable without jargon.Change Control —
A formal approval process for new features or math.Baseline Architecture —
The minimal, stable version of the system that all changes must respect.