cat >> /mnt/user-data/outputs/six_cylinder_boundary.py << 'PYEOF'


# ══════════════════════════════════════════════════════════════════════════════
# PWC SUBSTRATE INTERFACE
# ══════════════════════════════════════════════════════════════════════════════
# Exports the clean glue layer the PWC cognitive overlay needs.
# Nothing below reaches into internals — all state flows through
# the four typed structs and three interface functions.
# ──────────────────────────────────────────────────────────────────────────────

# ── Exported State Types ──────────────────────────────────────────────────────

@dataclass
class GSState:
    """Geometry solver snapshot — one instant of 6-face boundary state."""
    spin:              float
    pressure:          float
    temp:              float
    belt_mod:          float
    core_curvature:    float
    core_radius:       float
    core_throat:       float
    belt_curvature:    float
    belt_radius:       float
    cap_curvature:     float
    cap_radius:        float
    closed_loop_delta: float
    throat_velocity:   float
    timestamp:         float

    @classmethod
    def from_system_state(cls, state: SystemState,
                          solver: 'SixCylinderBoundary') -> 'GSState':
        return cls(
            spin=state.spin, pressure=state.pressure,
            temp=state.temp, belt_mod=state.belt_mod,
            core_curvature=state.core.curvature,
            core_radius=state.core.radius,
            core_throat=state.core.throat,
            belt_curvature=state.belt.curvature,
            belt_radius=state.belt.radius,
            cap_curvature=state.cap.curvature,
            cap_radius=state.cap.radius,
            closed_loop_delta=solver.closed_loop_delta(state),
            throat_velocity=solver.throat_velocity(state),
            timestamp=state.timestamp,
        )


@dataclass
class ManifoldState:
    """6D particle field snapshot — phase distribution + dimensional spread."""
    total_particles:  int
    intake_count:     int
    transit_count:    int
    exhaust_count:    int
    return_count:     int
    mean_x:           float
    mean_y:           float
    mean_z:           float
    mean_w:           float   # extended dim — spin axis carry
    mean_v:           float   # extended dim — temp coupling
    mean_u:           float   # extended dim — pressure coupling
    spatial_spread:   float   # std of x,y,z
    extended_spread:  float   # std of w,v,u
    timestamp:        float

    @classmethod
    def from_engine(cls, engine: 'ParticleFlowEngine6D') -> 'ManifoldState':
        counts = engine.phase_counts()
        if not engine.particles:
            return cls(0, 0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                       0.0, 0.0, time.time())
        data = engine.get_data_matrix()
        mean = data.mean(axis=0)
        spatial_spread  = float(np.std(data[:, :3]))
        extended_spread = float(np.std(data[:, 3:]))
        return cls(
            total_particles=len(engine.particles),
            intake_count=counts['INTAKE'],
            transit_count=counts['TRANSIT'],
            exhaust_count=counts['EXHAUST'],
            return_count=counts['RETURN'],
            mean_x=float(mean[0]), mean_y=float(mean[1]), mean_z=float(mean[2]),
            mean_w=float(mean[3]), mean_v=float(mean[4]), mean_u=float(mean[5]),
            spatial_spread=spatial_spread,
            extended_spread=extended_spread,
            timestamp=time.time(),
        )


@dataclass
class PIDState:
    """
    PID controller state for closed-loop spin / pressure / temp regulation.
    Tracks setpoint error, integral accumulation, and last derivative.
    """
    spin_setpoint:      float = 1.5
    pressure_setpoint:  float = 1.0
    temp_setpoint:      float = 0.0

    spin_error:         float = 0.0
    pressure_error:     float = 0.0
    temp_error:         float = 0.0

    spin_integral:      float = 0.0
    pressure_integral:  float = 0.0
    temp_integral:      float = 0.0

    spin_derivative:    float = 0.0
    pressure_derivative: float = 0.0
    temp_derivative:    float = 0.0

    # Output corrections — applied to next compute() call
    spin_correction:    float = 0.0
    pressure_correction: float = 0.0
    temp_correction:    float = 0.0

    timestamp:          float = field(default_factory=time.time)


@dataclass
class SafetyFlags:
    """
    System health and quarantine flags.
    Any True flag suppresses the corresponding axis in closed_loop_tick().
    """
    spin_quarantine:     bool  = False   # block spin mutations
    pressure_quarantine: bool  = False   # block pressure mutations
    temp_quarantine:     bool  = False   # block temp mutations
    pressure_cap_active: bool  = False   # pressure was clamped this tick
    relaxation_active:   bool  = False   # relaxation strength applied
    delta_violation:     bool  = False   # closed_loop_delta drifted > threshold
    stability_warning:   bool  = False   # stability < 0.99
    timestamp:           float = field(default_factory=time.time)


@dataclass
class LifecycleState:
    """Substrate lifecycle counters and health summary."""
    tick_count:          int   = 0
    uptime_seconds:      float = 0.0
    total_particles_spawned: int = 0
    quarantine_events:   int   = 0
    delta_violations:    int   = 0
    last_snapshot_time:  float = field(default_factory=time.time)
    healthy:             bool  = True


@dataclass
class SubstrateSnapshot:
    """Full substrate state — passed to the PWC cognitive layer each tick."""
    gs_state:        GSState
    manifold_state:  ManifoldState
    pid_state:       PIDState
    safety_flags:    SafetyFlags
    lifecycle_state: LifecycleState
    telemetry:       List[dict] = field(default_factory=list)


# ── PID Controller ────────────────────────────────────────────────────────────

class SubstratePID:
    """
    Simple PID for spin / pressure / temp axes.
    Kp, Ki, Kd tunable per axis.
    Integral windup clamped to ±max_integral.
    """

    def __init__(self,
                 kp=0.4, ki=0.05, kd=0.1,
                 max_integral=5.0,
                 max_correction=0.5):
        self.kp = kp; self.ki = ki; self.kd = kd
        self.max_integral  = max_integral
        self.max_correction = max_correction

    def update(self, pid: PIDState, gs: GSState, dt: float) -> PIDState:
        def _axis(setpoint, actual, integral, derivative, prev_error):
            error      = setpoint - actual
            integral   = max(-self.max_integral,
                             min(self.max_integral, integral + error * dt))
            derivative = (error - prev_error) / max(dt, 1e-6)
            correction = self.kp * error + self.ki * integral + self.kd * derivative
            correction = max(-self.max_correction, min(self.max_correction, correction))
            return error, integral, derivative, correction

        se, si, sd, sc = _axis(pid.spin_setpoint,     gs.spin,     pid.spin_integral,
                                pid.spin_derivative,   pid.spin_error)
        pe, pi_, pd, pc = _axis(pid.pressure_setpoint, gs.pressure, pid.pressure_integral,
                                pid.pressure_derivative, pid.pressure_error)
        te, ti, td, tc  = _axis(pid.temp_setpoint,     gs.temp,     pid.temp_integral,
                                pid.temp_derivative,   pid.temp_error)

        return PIDState(
            spin_setpoint=pid.spin_setpoint,
            pressure_setpoint=pid.pressure_setpoint,
            temp_setpoint=pid.temp_setpoint,
            spin_error=se,         pressure_error=pe,         temp_error=te,
            spin_integral=si,      pressure_integral=pi_,     temp_integral=ti,
            spin_derivative=sd,    pressure_derivative=pd,    temp_derivative=td,
            spin_correction=sc,    pressure_correction=pc,    temp_correction=tc,
            timestamp=time.time(),
        )


# ── Substrate Engine ──────────────────────────────────────────────────────────

class SubstrateEngine:
    """
    The PWC substrate interface.

    Wraps SixCylinderBoundary + ParticleFlowEngine6D + JEDNetworkBroker
    and exposes the three functions the cognitive layer needs:

        closed_loop_tick(...)   — apply PID, step physics, enforce safety
        snapshot_substrate()    — return SubstrateSnapshot
        get_recent_telemetry()  — return last N telemetry frames
    """

    DELTA_THRESHOLD   = 1e-9   # closed_loop_delta tolerance
    PRESSURE_CAP      = 2.0    # hard pressure ceiling
    RELAXATION_ALPHA  = 0.85   # exponential smoothing on relaxation

    def __init__(self,
                 base_radius:      float = 60.0,
                 particle_count:   int   = 300,
                 dt:               float = 0.04,
                 telemetry_maxlen: int   = 200,
                 broker:           Optional['JEDNetworkBroker'] = None,
                 pid_kp: float = 0.4, pid_ki: float = 0.05, pid_kd: float = 0.1):

        self.boundary  = SixCylinderBoundary(base_radius)
        self.engine    = ParticleFlowEngine6D(particle_count)
        self.broker    = broker
        self.dt        = dt
        self._pid_ctrl = SubstratePID(kp=pid_kp, ki=pid_ki, kd=pid_kd)

        # Mutable state
        self._pid      = PIDState()
        self._safety   = SafetyFlags()
        self._lifecycle = LifecycleState()
        self._telemetry_ring: List[dict] = []
        self._telemetry_maxlen = telemetry_maxlen
        self._start_time = time.time()
        self._lock = threading.Lock()

    # ── Primary Interface ─────────────────────────────────────────────────────

    def closed_loop_tick(
        self,
        spin:             float = None,
        pressure:         float = None,
        temp:             float = None,
        belt_mod:         float = None,
        relaxation_strength: float = 1.0,
        quarantine_spin:  bool  = False,
        quarantine_pressure: bool = False,
        quarantine_temp:  bool  = False,
    ) -> SubstrateSnapshot:
        """
        One full closed-loop tick:
          1. Read last GS state.
          2. Update PID errors and compute corrections.
          3. Apply corrections (unless quarantined).
          4. Enforce pressure cap.
          5. Apply relaxation strength (smoothing toward setpoint).
          6. Step geometry solver.
          7. Step particle engine.
          8. Update safety flags.
          9. Update lifecycle counters.
         10. Push telemetry.
         11. Return SubstrateSnapshot.
        """
        with self._lock:
            last = self.boundary.last_state
            if last is None:
                last = self.boundary.compute(
                    spin     = spin     or self._pid.spin_setpoint,
                    pressure = pressure or self._pid.pressure_setpoint,
                    temp     = temp     or self._pid.temp_setpoint,
                    belt_mod = belt_mod or 1.0,
                )

            gs = GSState.from_system_state(last, self.boundary)

            # ── 1. PID update ─────────────────────────────────────────────────
            self._pid = self._pid_ctrl.update(self._pid, gs, self.dt)

            # ── 2. Resolve target params ──────────────────────────────────────
            # External override > PID-corrected setpoint > last state
            def _resolve(override, setpoint, correction, quarantined, last_val):
                if quarantined:   return last_val
                if override is not None: return override
                return setpoint + correction * relaxation_strength

            target_spin = _resolve(
                spin,     self._pid.spin_setpoint,
                self._pid.spin_correction,     quarantine_spin,     last.spin)
            target_pressure = _resolve(
                pressure, self._pid.pressure_setpoint,
                self._pid.pressure_correction, quarantine_pressure, last.pressure)
            target_temp = _resolve(
                temp,     self._pid.temp_setpoint,
                self._pid.temp_correction,     quarantine_temp,     last.temp)
            target_belt = belt_mod if belt_mod is not None else last.belt_mod

            # ── 3. Pressure cap ───────────────────────────────────────────────
            pressure_capped = target_pressure > self.PRESSURE_CAP
            if pressure_capped:
                target_pressure = self.PRESSURE_CAP

            # ── 4. Step geometry ──────────────────────────────────────────────
            new_state = self.boundary.compute(
                spin=target_spin, pressure=target_pressure,
                temp=target_temp, belt_mod=target_belt,
            )

            # ── 5. Step particles ─────────────────────────────────────────────
            self.engine.step(new_state, dt=self.dt)

            # ── 6. Safety flags ───────────────────────────────────────────────
            delta     = self.boundary.closed_loop_delta(new_state)
            metrics   = self.boundary.to_toroidal_metrics(new_state)
            stability = metrics['closed_loop_stability']

            delta_viol = abs(delta) > self.DELTA_THRESHOLD
            stab_warn  = stability < 0.99

            self._safety = SafetyFlags(
                spin_quarantine=quarantine_spin,
                pressure_quarantine=quarantine_pressure,
                temp_quarantine=quarantine_temp,
                pressure_cap_active=pressure_capped,
                relaxation_active=(relaxation_strength != 1.0),
                delta_violation=delta_viol,
                stability_warning=stab_warn,
                timestamp=time.time(),
            )

            # ── 7. Lifecycle ──────────────────────────────────────────────────
            self._lifecycle.tick_count += 1
            self._lifecycle.uptime_seconds = time.time() - self._start_time
            self._lifecycle.total_particles_spawned += len(self.engine.particles)
            if quarantine_spin or quarantine_pressure or quarantine_temp:
                self._lifecycle.quarantine_events += 1
            if delta_viol:
                self._lifecycle.delta_violations += 1
            self._lifecycle.healthy = not delta_viol and not stab_warn
            self._lifecycle.last_snapshot_time = time.time()

            # ── 8. Telemetry ring ─────────────────────────────────────────────
            frame = {
                'tick':       self._lifecycle.tick_count,
                'timestamp':  new_state.timestamp,
                'spin':       new_state.spin,
                'pressure':   new_state.pressure,
                'temp':       new_state.temp,
                'stability':  stability,
                'core_throat': new_state.core.throat,
                'belt_radius': new_state.belt.radius,
                'delta':      delta,
                'healthy':    self._lifecycle.healthy,
            }
            self._telemetry_ring.append(frame)
            if len(self._telemetry_ring) > self._telemetry_maxlen:
                self._telemetry_ring.pop(0)

            if self.broker:
                self.broker.push_telemetry(new_state, metrics)

            return self.snapshot_substrate()

    def snapshot_substrate(self) -> SubstrateSnapshot:
        """Return a full typed snapshot of current substrate state."""
        with self._lock:
            last = self.boundary.last_state or self.boundary.compute()
            return SubstrateSnapshot(
                gs_state       = GSState.from_system_state(last, self.boundary),
                manifold_state = ManifoldState.from_engine(self.engine),
                pid_state      = self._pid,
                safety_flags   = self._safety,
                lifecycle_state= self._lifecycle,
                telemetry      = list(self._telemetry_ring[-10:]),
            )

    def get_recent_telemetry(self, n: int = 50) -> List[dict]:
        """Return the last n telemetry frames from the async ring buffer."""
        with self._lock:
            return list(self._telemetry_ring[-n:])

    # ── Setpoint control (for PWC to drive) ──────────────────────────────────

    def set_setpoints(self, spin: float = None, pressure: float = None,
                      temp: float = None):
        """PWC cognitive layer calls this to steer the substrate."""
        with self._lock:
            if spin     is not None: self._pid.spin_setpoint     = spin
            if pressure is not None: self._pid.pressure_setpoint = pressure
            if temp     is not None: self._pid.temp_setpoint     = temp
PYEOF
echo "done"