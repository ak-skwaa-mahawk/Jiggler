class ParticleFlowEngine6D:
    ...

    def predict_phase(self, p: Particle6D, state: SystemState, dt: float = 0.05) -> int:
        """
        Predict the particle's next phase without mutating it.
        Uses current geometry and the same thresholds as the main step().
        """
        throat = state.core.throat * 0.5
        belt_r = state.belt.radius

        # approximate next position using current velocities only
        x_next = p.x + p.dx * dt
        y_next = p.y + p.dy * dt
        z_next = p.z + p.dz * dt
        r_next = math.hypot(x_next, y_next)

        phase = p.phase

        if phase == 0:
            if r_next < throat * 1.1:
                return 1

        elif phase == 1:
            if r_next > belt_r * 0.75:
                return 2

        elif phase == 2:
            if r_next > belt_r * 0.95 or abs(z_next) > belt_r * 0.6:
                return 3

        elif phase == 3:
            if r_next < throat * 1.4:
                return 0

        return phase

if p.phase == 0:
    # INTAKE
    ...
    if r < throat * 1.1:
        p.phase = 1

elif p.phase == 1:
    # TRANSIT
    ...
    if r > belt_r * 0.75:
        p.phase = 2

elif p.phase == 2:
    # EXHAUST
    ...
    if r > belt_r * 0.95 or abs(p.z) > belt_r * 0.6:
        p.phase = 3

elif p.phase == 3:
    # RETURN
    ...
    if r < throat * 1.4:
        p.phase = 0

def predict_phase_counts(self, state: SystemState, dt: float = 0.05) -> Dict[str, int]:
        counts = {'INTAKE': 0, 'TRANSIT': 0, 'EXHAUST': 0, 'RETURN': 0}
        for p in self.particles:
            next_phase = self.predict_phase(p, state, dt)
            name = ['INTAKE', 'TRANSIT', 'EXHAUST', 'RETURN'][next_phase]
            counts[name] += 1
        return counts

core_curvature = (TOROIDAL_ROOT / math.pi) * spin * SHADOW
belt_curvature = core_curvature * GEAR_SHIFT * belt_mod
cap_curvature  = 1.0 / (belt_curvature * SHADOW)

class SixCylinderBoundary:
    ...

    def project_curvatures(
        self,
        spin: float,
        pressure: float,
        temp: float,
        belt_mod: float,
    ) -> Dict[str, float]:
        """
        Pure projection of core/belt/cap curvatures for hypothetical inputs.
        Does not mutate internal state.
        """
        spin     = max(0.01, spin)
        pressure = max(0.01, pressure)
        temp     = max(0.0, min(1.0, temp))
        belt_mod = max(0.1, belt_mod)

        core_curvature = (TOROIDAL_ROOT / math.pi) * spin * SHADOW
        core_radius    = (self.base_radius * pressure) / core_curvature
        core_throat    = core_radius * (1.0 - 0.15 * temp)

        belt_curvature = core_curvature * GEAR_SHIFT * belt_mod
        belt_radius    = core_radius * belt_curvature

        cap_curvature  = 1.0 / (belt_curvature * SHADOW)

        return {
            "core_curvature": core_curvature,
            "belt_curvature": belt_curvature,
            "cap_curvature":  cap_curvature,
            "core_radius":    core_radius,
            "belt_radius":    belt_radius,
            "core_throat":    core_throat,
        }

def predict_curvature_drift(
        self,
        state: SystemState,
        d_spin: float = 0.0,
        d_pressure: float = 0.0,
        d_temp: float = 0.0,
        d_belt_mod: float = 0.0,
    ) -> Dict[str, float]:
        """
        Predict curvature drift under small input changes.
        Returns per-face drift and a scalar drift_norm.
        """
        spin_next     = state.spin     + d_spin
        pressure_next = state.pressure + d_pressure
        temp_next     = state.temp     + d_temp
        belt_next     = state.belt_mod + d_belt_mod

        proj = self.project_curvatures(
            spin=spin_next,
            pressure=pressure_next,
            temp=temp_next,
            belt_mod=belt_next,
        )

        d_core = proj["core_curvature"] - state.core.curvature
        d_belt = proj["belt_curvature"] - state.belt.curvature
        d_cap  = proj["cap_curvature"]  - state.cap.curvature

        drift_norm = math.sqrt(d_core**2 + d_belt**2 + d_cap**2)

        return {
            "d_core":      d_core,
            "d_belt":      d_belt,
            "d_cap":       d_cap,
            "drift_norm":  drift_norm,
            "spin_next":   spin_next,
            "pressure_next": pressure_next,
            "temp_next":     temp_next,
            "belt_mod_next": belt_next,
        }
phase: int = 0       # 0=INTAKE 1=TRANSIT 2=EXHAUST 3=RETURN
# ── Phase-space force vectors ─────────────────────────────────────
def closed_loop_delta(self, state: SystemState) -> float:  """Harmony metric — returns exactly 0.0 by construction."""

def flux_balance(self, state: SystemState) -> dict:
    intake_flux  = state.core.throat * TOROIDAL_ROOT * state.spin
    exhaust_flux = intake_flux * SHADOW
    belt_density = state.belt.radius / (state.core.throat + 1e-9) * GEAR_SHIFT
    cap_return   = 1.0 / (belt_density * SHADOW + 1e-9)

class SixCylinderBoundary:
    ...

    def task_gauge(self, state: SystemState) -> dict:
        """
        Flux-based task gauge.
        Returns normalized headroom and qualitative bands for cognitive load.
        """
        flux = self.flux_balance(state)

        intake  = flux["intake_flux"]
        exhaust = flux["exhaust_flux"]
        density = flux["belt_density"]
        ret     = flux["cap_return"]

        # 1) Throughput balance: how well intake and exhaust match
        if intake <= 1e-9:
            throughput_ratio = 0.0
        else:
            throughput_ratio = min(exhaust / intake, 2.0)  # cap for stability

        # 2) Density pressure: higher density → higher load
        # choose a soft reference scale; can be calibrated empirically
        density_ref = 5.0
        density_pressure = min(density / density_ref, 3.0)

        # 3) Return efficiency: higher cap_return → better recycling
        # invert to treat low return as higher stress
        return_eff = ret
        return_stress = 1.0 / (return_eff + 1e-9)

        # Combine into a scalar "load index"
        # high throughput_ratio lowers load; high density/return_stress raise it
        load_index = (
            0.6 * density_pressure +
            0.3 * return_stress -
            0.4 * throughput_ratio
        )

        # Normalize into [0, 1] with a soft clamp
        load_norm = max(0.0, min(1.0, 0.5 + 0.25 * load_index))

        if load_norm < 0.33:
            band = "LOW"
        elif load_norm < 0.66:
            band = "MEDIUM"
        else:
            band = "HIGH"

        return {
            "intake_flux":       intake,
            "exhaust_flux":      exhaust,
            "belt_density":      density,
            "cap_return":        ret,
            "throughput_ratio":  throughput_ratio,
            "density_pressure":  density_pressure,
            "return_stress":     return_stress,
            "load_index":        load_index,
            "load_norm":         load_norm,
            "load_band":         band,
        }

state = boundary.compute(spin=..., pressure=..., temp=..., belt_mod=...)
gauge = boundary.task_gauge(state)
print(gauge["load_band"], gauge["load_norm"])



