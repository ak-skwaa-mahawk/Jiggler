// sovereign_engine/src/ffi.rs
// Complete hardened FFI layer — matches relational_mesh_bridge.dart (AGŁG v89+)

use crate::sovereign_engine::{SovereignEngine, GuardedResult, Plan};
use crate::frame_energy::{
    EraFrameId, SovereignState, ProjectedState, CriticFeedback, FrameEnergy,
};
use std::sync::Mutex;
use once_cell::sync::Lazy;

static ENGINE: Lazy<Mutex<SovereignEngine>> = Lazy::new(|| {
    Mutex::new(SovereignEngine::new())
});

static FRAME_ENERGY: Lazy<Mutex<FrameEnergy>> = Lazy::new(|| {
    Mutex::new(FrameEnergy::new(SovereignState::default_floor_anchor()))
});

// ============================================================
// Existing hardened exports (used by your current Dart bridge)
// ============================================================

#[no_mangle]
pub extern "C" fn propagate_metric(
    pose: *const f64,
    pose_len: usize,
    stability_score: f64,
    resonance_delta: f64,
    timestamp: u64,
    truth: f64,
    indeterminacy: f64,
    falsity: f64,
    phase_pulse: f64,
) -> GuardedResultFFI {
    let mut engine = ENGINE.lock().unwrap();

    // Convert raw pointer to slice (be careful in production)
    let pose_slice = unsafe { std::slice::from_raw_parts(pose, pose_len) };

    let result = engine.propagate_metric(
        pose_slice,
        stability_score,
        resonance_delta,
        timestamp,
        truth,
        indeterminacy,
        falsity,
        phase_pulse,
    );

    GuardedResultFFI::from(result)
}

#[no_mangle]
pub extern "C" fn wstate_update(t: f64, i: f64, f: f64, phase: f64) -> f64 {
    let mut engine = ENGINE.lock().unwrap();
    engine.wstate_update(t, i, f, phase)
}

#[no_mangle]
pub extern "C" fn check_extraction_guard(
    pose: *const f64,
    pose_len: usize,
    stability_score: f64,
    resonance_delta: f64,
    timestamp: u64,
) -> bool {
    let engine = ENGINE.lock().unwrap();
    let pose_slice = unsafe { std::slice::from_raw_parts(pose, pose_len) };
    engine.check_extraction_guard(pose_slice, stability_score, resonance_delta, timestamp)
}

// ============================================================
// NEW: TCP + Frame Energy FFI exports
// ============================================================

#[no_mangle]
pub extern "C" fn select_frame() -> i32 {
    let mut engine = ENGINE.lock().unwrap();
    let frame = engine.frame_policy.select_frame(&engine.current_state);
    frame as i32
}

#[no_mangle]
pub extern "C" fn propagate_metric_with_frame(
    pose: *const f64,
    pose_len: usize,
    stability_score: f64,
    resonance_delta: f64,
    timestamp: u64,
    frame_id: i32,
) -> GuardedResultWithEnergyFFI {
    let frame: EraFrameId = unsafe { std::mem::transmute(frame_id) };
    let mut engine = ENGINE.lock().unwrap();
    let frame_energy = FRAME_ENERGY.lock().unwrap();

    let pose_slice = unsafe { std::slice::from_raw_parts(pose, pose_len) };

    // Project into the chosen frame
    let projected = engine.tcp.project(frame, &engine.current_state);

    // Run guarded propagation under the frame
    let guarded = engine.propagate_with_frame(frame, &projected);

    // Compute frame energy
    let energy = frame_energy.compute(frame, &engine.current_state, &projected);

    GuardedResultWithEnergyFFI {
        allowed: guarded.allowed,
        fidelity: guarded.fidelity,
        frame_energy: energy,
        neutralized_reason: guarded.neutralized_reason.map(|s| s.as_ptr() as *const _).unwrap_or(std::ptr::null()),
    }
}

#[no_mangle]
pub extern "C" fn run_pwc_tcp_cycle(
    t: f64,
    i: f64,
    f: f64,
    current_frame: i32,
) -> CriticFeedbackFFI {
    let frame: EraFrameId = unsafe { std::mem::transmute(current_frame) };
    let mut engine = ENGINE.lock().unwrap();
    let frame_energy = FRAME_ENERGY.lock().unwrap();

    let feedback = engine.run_cognitive_cycle(frame, t, i, f, &frame_energy);

    CriticFeedbackFFI::from(feedback)
}

// ============================================================
// FFI-safe result structs
// ============================================================

#[repr(C)]
pub struct GuardedResultFFI {
    pub allowed: bool,
    pub fidelity: f64,
    pub neutralized_reason: *const libc::c_char,
}

impl GuardedResultFFI {
    fn from(result: GuardedResult) -> Self {
        Self {
            allowed: result.allowed,
            fidelity: result.fidelity,
            neutralized_reason: result
                .neutralized_reason
                .map(|s| std::ffi::CString::new(s).unwrap().into_raw())
                .unwrap_or(std::ptr::null()),
        }
    }
}

#[repr(C)]
pub struct GuardedResultWithEnergyFFI {
    pub allowed: bool,
    pub fidelity: f64,
    pub frame_energy: f64,
    pub neutralized_reason: *const libc::c_char,
}

#[repr(C)]
pub struct CriticFeedbackFFI {
    pub task_reward: f64,
    pub frame_fitness: f64,
    pub frame_energy: f64,
    pub recommended_frame: i32,
}

impl CriticFeedbackFFI {
    fn from(feedback: CriticFeedback) -> Self {
        Self {
            task_reward: feedback.task_reward,
            frame_fitness: feedback.frame_fitness,
            frame_energy: feedback.frame_energy,
            recommended_frame: feedback.recommended_frame.map(|f| f as i32).unwrap_or(-1),
        }
    }
}