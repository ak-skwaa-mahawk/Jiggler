1. TYPE SYSTEMAll types are expressed in a language‑agnostic structural form.1.1 Scalar TypesFloat64 — double‑precision realInt64 — signed integerBool — booleanTimestamp — monotonic or wall‑clock timeUUID — unique identifier1.2 Vector & Field TypesVecN[N] — fixed‑length vector of Float64Field1D — array of Float64Field2D — matrix of Float64Field3D — tensor of Float641.3 Core Domain TypesGSStateCopyGSState {
    generators: Int64
    relations: Int64
    pressure_field: Field2D
    regime: GSRegime
    diagnostics: GSDiagnostics
}GSRegimeCopyenum GSRegime {
    NORMAL
    CLAMPED
    RELAXED
    QUARANTINED
}GSDiagnosticsCopyGSDiagnostics {
    divergence_indicator: Float64
    saturation_count: Int64
    local_growth_rate: Float64
}TordialNodeStateCopyTordialNodeState {
    curvature: Float64
    drift: Float64
    gs_pressure_local: Float64
    safety_flags: SafetyFlags
}SafetyFlagsCopySafetyFlags {
    drift_exceeded: Bool
    pressure_exceeded: Bool
    spectral_instability: Bool
    quarantined: Bool
}PIDStateCopyPIDState {
    error: Float64
    integral: Float64
    derivative: Float64
    output: Float64
}ManifoldStateCopyManifoldState {
    nodes: array<TordialNodeState>
    global_drift: Float64
    curvature_field: Field2D
    gs_pressure_global: Float64
}2. FUNCTION SIGNATURES2.1 GS ENGINE INTERFACEgs_init(version: Int64) → GSStateInitialize a GS engine instance.gs_step(state: GSState, feedback: GSFeedback) → GSStatePerform one micro‑step of GS evolution.GSFeedbackCopyGSFeedback {
    drift: Float64
    curvature: Float64
    pid_output: Float64
    pressure_cap: Float64
}gs_clamp(state: GSState, cap: Float64) → GSStateApply clamping to pressure field.gs_relax(state: GSState, relaxation_strength: Float64) → GSStateApply PDE/spectral relaxation.gs_quarantine(state: GSState) → GSStateForce GS into QUARANTINED regime.2.2 TORDIAL MACRO‑GEOMETRY INTERFACEtordial_init(node_count: Int64) → ManifoldStateInitialize toroidal manifold.tordial_update(state: ManifoldState, gs_state: GSState) → ManifoldStateUpdate curvature, drift, and node‑level metrics based on GS output.compute_drift(state: ManifoldState) → Float64Compute global drift.compute_curvature(state: ManifoldState) → Field2DCompute curvature field.apply_pid(state: ManifoldState, pid: PIDState) → ManifoldStateApply PID output to manifold parameters.2.3 CLOSED‑LOOP CONTROLLER INTERFACEpid_step(pid: PIDState, error: Float64, dt: Float64) → PIDStateStandard PID update.compute_feedback(gs: GSState, manifold: ManifoldState, pid: PIDState) → GSFeedbackGenerate GS feedback control signals.closed_loop_tick(gs: GSState, manifold: ManifoldState, pid: PIDState, dt: Float64) → (GSState, ManifoldState, PIDState)Atomic closed‑loop update.2.4 SAFETY & LIFECYCLE INTERFACEsafety_evaluate(gs: GSState, manifold: ManifoldState) → SafetyFlagsEvaluate safety conditions.lifecycle_transition(current: LifecycleState, flags: SafetyFlags) → LifecycleStateTransition lifecycle state.LifecycleStateCopyenum LifecycleState {
    INIT
    RUNNING
    DEGRADED
    SAFE_SHUTDOWN
    QUARANTINED
}3. DISTRIBUTED RPC PROTOCOL (PROTOBUF SCHEMA)
---

3.1 Messages

GSStateMessage
`
message GSStateMessage {
    int64 generators = 1;
    int64 relations = 2;
    repeated float pressure_field = 3; // flattened 2D
    string regime = 4;
    float divergence_indicator = 5;
    float localgrowthrate = 6;
}
`

---

ManifoldStateMessage
`
message ManifoldStateMessage {
    repeated float curvature_field = 1; // flattened 2D
    repeated float drift_field = 2;     // flattened 2D
    float global_drift = 3;
    float global_pressure = 4;
    repeated SafetyFlagsMessage safety = 5;
}
`

---

SafetyFlagsMessage
`
message SafetyFlagsMessage {
    bool drift_exceeded = 1;
    bool pressure_exceeded = 2;
    bool spectral_instability = 3;
    bool quarantined = 4;
}
`

---

PIDMessage
`
message PIDMessage {
    float error = 1;
    float integral = 2;
    float derivative = 3;
    float output = 4;
}
`

---

ControlCommand
`
message ControlCommand {
    float pid_output = 1;
    float pressure_cap = 2;
    float relaxation_strength = 3;
    bool quarantine = 4;
}
`

---

3.2 RPC Services

TordialNodeService
`
service TordialNodeService {
    rpc StreamState(stream NodeStateRequest) returns (stream NodeStateResponse);
    rpc SendControl(ControlCommand) returns (Ack);
}
`

---

DistributedControllerService
`
service DistributedControllerService {
    rpc BroadcastPID(PIDMessage) returns (Ack);
    rpc CollectTelemetry(TelemetryRequest) returns (TelemetryResponse);
}
`

---

4. TELEMETRY & LOGGING INTERFACE

TelemetryRecord
`
TelemetryRecord {
    timestamp: Timestamp
    node_id: UUID
    drift: Float64
    curvature: Float64
    gs_pressure: Float64
    pid_output: Float64
    safety: SafetyFlags
}
`

---

telemetry_emit(record: TelemetryRecord) → void
Emit telemetry asynchronously.

---

telemetry_query(filter: TelemetryFilter) → array<TelemetryRecord>
Query historical telemetry.

---

5. VISUALIZATION INTERFACE

visual_update(state: ManifoldState, gs: GSState) → VisualFrame
`
VisualFrame {
    curvature_field: Field2D
    drift_field: Field2D
    pressure_field: Field2D
    safety_overlay: Field2D
}
`

---

6. EXTENSION POINTS

GS Plugin Interface
`
GSPlugin {
    init() → PluginState
    step(state: PluginState, gs: GSState, manifold: ManifoldState) → PluginState
    modify_feedback(feedback: GSFeedback) → GSFeedback
}
`

---

Controller Plugin Interface
`
ControllerPlugin {
    compute_control(manifold: ManifoldState, gs: GSState) → ControlCommand
}
`

---

7. VERSIONING RULES

- Every GS engine version must declare:
  - Supported feedback fields
  - Pressure field dimensionality
  - Relaxation model
- RPC messages must include:
  `
  int32 protocol_version = 999;
  `

---

