
---

🧱 Tordial‑GS CONTRIBUTING.md

(Engineering‑Grounded, Anti‑Technobabble Edition)

---

📌 1. Project Philosophy

Tordial‑GS is a numerical spectral solver and multi‑node simulation framework.  
It is not a metaphysical system, symbolic cosmology, or experimental math playground.

All contributions must align with:

- Plain‑language engineering  
- Deterministic numerical methods  
- Standard scientific computing practices  
- Minimal conceptual overhead  
- Zero speculative terminology

If a contribution cannot be explained in two sentences of plain English, it does not enter the codebase.

---

🛑 2. Anti‑Technobabble Policy

To prevent conceptual drift, all contributors must follow these rules:

2.1 Allowed
- Standard numerical terms  
- Standard PDE terminology  
- Standard spectral methods  
- Standard distributed‑systems vocabulary  

2.2 Not Allowed
- Invented terminology  
- Metaphorical system names  
- Undefined symbolic constants  
- Speculative physics or math  
- Narrative or mythic framing  

2.3 Enforcement Rule
If a term cannot be mapped to a real engineering concept in the Tordial‑GS Glossary, it must be renamed or removed.

---

📐 3. Scope Boundaries

The following items are explicitly out of scope:

- No new “manifold types” beyond the 2D torus grid  
- No symbolic algebra engines  
- No custom physics models  
- No invented mathematical operators  
- No AI‑driven “emergent behavior” modules  
- No speculative control systems  

If you want to propose a new feature, it must map to a real, documented numerical method.

---

🧪 4. Code Requirements

4.1 Determinism
All code must produce deterministic results given fixed inputs.

4.2 Test Coverage
Every PR must include:

- Unit tests  
- Integration tests (if applicable)  
- Benchmarks for performance‑critical code  

Use:

- Rust: cargo test  
- Python: pytest  

4.3 Documentation
All functions must include:

- Plain‑language description  
- Input/output definitions  
- Failure modes  
- Complexity notes (if non‑trivial)

No metaphors. No narrative. No invented vocabulary.

---

🧰 5. Architecture Rules

5.1 Core Solver
The spectral solver must remain:

- FFT‑based  
- Linear  
- Explicit  
- Stable  
- Minimal  

No nonlinear PDEs unless justified with real‑world use cases.

5.2 Cluster Layer
The cluster system must:

- Only exchange low‑frequency modes  
- Use simple averaging  
- Avoid speculative distributed algorithms  

5.3 Python FFI
The PyO3 layer must:

- Expose only stable APIs  
- Avoid leaking Rust internals  
- Use NumPy arrays exclusively for data interchange  

---

🔒 6. Change Control

All changes must pass through:

1. Proposal  
   - Describe the change in plain English  
   - Map it to a real numerical method  
   - Provide a minimal example

2. Review  
   - Must be approved by maintainers  
   - Must not expand conceptual scope

3. Validation  
   - Tests must pass  
   - Benchmarks must not regress  
   - Documentation must be updated

4. Merge  
   - Squash commits  
   - Include a clear commit message  

---

🧹 7. Code Hygiene

- No dead code  
- No unused constants  
- No placeholder modules  
- No commented‑out blocks  
- No speculative TODOs  
- No unexplained magic numbers  

If it’s not used, it’s removed.

---

📦 8. Dependencies

Allowed:

- RustFFT  
- NumPy  
- PyO3  
- Criterion  
- ndarray  

Not allowed:

- Experimental math libraries  
- Symbolic algebra engines  
- ML frameworks  
- GPU frameworks (unless explicitly approved)

---

🧭 9. Contribution Workflow

1. Fork the repo  
2. Create a feature branch  
3. Implement changes  
4. Add tests  
5. Add benchmarks  
6. Update docs  
7. Submit PR  
8. Pass review  
9. Merge  

---

🧩 10. Glossary Requirement

All new terms must be added to the Tordial‑GS Glossary before merging.

If a term cannot be defined in plain language, it is rejected.

---

✔️ This CONTRIBUTING.md is now ready to drop into your repo.

If you want, I can also generate:

- Project Charter  
- Full repo scaffold  
- Test suite  

Just pick the next piece.Below is a clean, enforceable, engineering‑grounded CONTRIBUTING.md for the Tordial‑GS project.  
It is written to stop technobabble, prevent scope creep, and ensure the codebase stays practical, testable, and maintainable.  
Every rule is actionable, and every section includes Guided Links so you can expand or refine policies later.

---

🧱 Tordial‑GS CONTRIBUTING.md

(Engineering‑Grounded, Anti‑Technobabble Edition)

---

📌 1. Project Philosophy

Tordial‑GS is a numerical spectral solver and multi‑node simulation framework.  
It is not a metaphysical system, symbolic cosmology, or experimental math playground.

All contributions must align with:

- Plain‑language engineering  
- Deterministic numerical methods  
- Standard scientific computing practices  
- Minimal conceptual overhead  
- Zero speculative terminology

If a contribution cannot be explained in two sentences of plain English, it does not enter the codebase.

---

🛑 2. Anti‑Technobabble Policy

To prevent conceptual drift, all contributors must follow these rules:

2.1 Allowed
- Standard numerical terms  
- Standard PDE terminology  
- Standard spectral methods  
- Standard distributed‑systems vocabulary  

2.2 Not Allowed
- Invented terminology  
- Metaphorical system names  
- Undefined symbolic constants  
- Speculative physics or math  
- Narrative or mythic framing  

2.3 Enforcement Rule
If a term cannot be mapped to a real engineering concept in the Tordial‑GS Glossary, it must be renamed or removed.

---

📐 3. Scope Boundaries

The following items are explicitly out of scope:

- No new “manifold types” beyond the 2D torus grid  
- No symbolic algebra engines  
- No custom physics models  
- No invented mathematical operators  
- No AI‑driven “emergent behavior” modules  
- No speculative control systems  

If you want to propose a new feature, it must map to a real, documented numerical method.

---

🧪 4. Code Requirements

4.1 Determinism
All code must produce deterministic results given fixed inputs.

4.2 Test Coverage
Every PR must include:

- Unit tests  
- Integration tests (if applicable)  
- Benchmarks for performance‑critical code  

Use:

- Rust: cargo test  
- Python: pytest  

4.3 Documentation
All functions must include:

- Plain‑language description  
- Input/output definitions  
- Failure modes  
- Complexity notes (if non‑trivial)

No metaphors. No narrative. No invented vocabulary.

---

🧰 5. Architecture Rules

5.1 Core Solver
The spectral solver must remain:

- FFT‑based  
- Linear  
- Explicit  
- Stable  
- Minimal  

No nonlinear PDEs unless justified with real‑world use cases.

5.2 Cluster Layer
The cluster system must:

- Only exchange low‑frequency modes  
- Use simple averaging  
- Avoid speculative distributed algorithms  

5.3 Python FFI
The PyO3 layer must:

- Expose only stable APIs  
- Avoid leaking Rust internals  
- Use NumPy arrays exclusively for data interchange  

---

🔒 6. Change Control

All changes must pass through:

1. Proposal  
   - Describe the change in plain English  
   - Map it to a real numerical method  
   - Provide a minimal example

2. Review  
   - Must be approved by maintainers  
   - Must not expand conceptual scope

3. Validation  
   - Tests must pass  
   - Benchmarks must not regress  
   - Documentation must be updated

4. Merge  
   - Squash commits  
   - Include a clear commit message  

---

🧹 7. Code Hygiene

- No dead code  
- No unused constants  
- No placeholder modules  
- No commented‑out blocks  
- No speculative TODOs  
- No unexplained magic numbers  

If it’s not used, it’s removed.

---

📦 8. Dependencies

Allowed:

- RustFFT  
- NumPy  
- PyO3  
- Criterion  
- ndarray  

Not allowed:

- Experimental math libraries  
- Symbolic algebra engines  
- ML frameworks  
- GPU frameworks (unless explicitly approved)

---

🧭 9. Contribution Workflow

1. Fork the repo  
2. Create a feature branch  
3. Implement changes  
4. Add tests  
5. Add benchmarks  
6. Update docs  
7. Submit PR  
8. Pass review  
9. Merge  

---

🧩 10. Glossary Requirement

All new terms must be added to the Tordial‑GS Glossary before merging.

If a term cannot be defined in plain language, it is rejected.

---

