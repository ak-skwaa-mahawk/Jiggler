use std::ffi::{CString};
use std::os::raw::c_char;

/// Data Structures (Input - Must perfectly map to C-FFI struct packing)
#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub struct SovereignMetric {
    pub pose: [f64; 3],          // pose[0] = d, pose[1] = r, pose[2] = sigma_t
    pub stability_score: f64,    // maps directly to rho
    pub resonance_delta: f64,    // maps directly to intent_value / delta validation
    pub timestamp: u64,          // operational lifecycle timestamp
}

#[repr(C)]
#[derive(Debug, Clone, Copy)]
pub struct DerivedMetric {
    pub optimized_resonance: f64,
    pub lifecycle_epoch: u64,
}

/// Data Structures (Output - Boundary container matches 32-byte AAPCS64 spec)
#[repr(C)]
pub struct GuardedOutput {
    pub allowed: bool,
    pub fidelity: f64,
    pub neutralized_reason: *const c_char,
    pub derived_metric: *mut DerivedMetric,
}

// Global Static Basin Boundary Constraints
pub struct BasinBounds {
    pub d_min: f64,
    pub d_max: f64,
    pub r_min: f64,
    pub r_max: f64,
    pub sigma_t_min: f64,
    pub sigma_t_max: f64,
    pub rho_min: f64,
    pub rho_max: f64,
}

const BOUNDS: BasinBounds = BasinBounds {
    d_min: 24.0,
    d_max: 30.0,
    r_min: 140.0,
    r_max: 180.0,
    sigma_t_min: 50.0,
    sigma_t_max: 70.0,
    rho_min: 0.31,
    rho_max: 0.34,
};

#[no_mangle]
pub extern "C" fn check_extraction_guard(metric: *const SovereignMetric) -> GuardedOutput {
    if metric.is_null() {
        return GuardedOutput {
            allowed: false,
            fidelity: 0.0,
            neutralized_reason: CString::new("Null input metric block").unwrap().into_raw(),
            derived_metric: std::ptr::null_mut(),
        };
    }

    let m = unsafe { &*metric };
    
    // Extract state variables from the incoming metric payload layout
    let current_d = m.pose[0];
    let current_r = m.pose[1];
    let current_sigma_t = m.pose[2];
    let current_rho = m.stability_score;
    let baseline_intent = m.resonance_delta;

    // 1. Calculate Euclidean distance to the attractor ridge
    let d_dist = if current_d < BOUNDS.d_min { BOUNDS.d_min - current_d } else if current_d > BOUNDS.d_max { current_d - BOUNDS.d_max } else { 0.0 };
    let r_dist = if current_r < BOUNDS.r_min { BOUNDS.r_min - current_r } else if current_r > BOUNDS.r_max { current_r - BOUNDS.r_max } else { 0.0 };
    let sigma_dist = if current_sigma_t < BOUNDS.sigma_t_min { BOUNDS.sigma_t_min - current_sigma_t } else if current_sigma_t > BOUNDS.sigma_t_max { current_sigma_t - BOUNDS.sigma_t_max } else { 0.0 };
    let rho_dist = if current_rho < BOUNDS.rho_min { BOUNDS.rho_min - current_rho } else if current_rho > BOUNDS.rho_max { current_rho - BOUNDS.rho_max } else { 0.0 };

    let distance = (d_dist.powi(2) + r_dist.powi(2) + sigma_dist.powi(2) + rho_dist.powi(2)).sqrt();

    // 2. Compute smooth roll-off damping factor based on ridge distance
    let damping_factor = if distance <= 1.5 {
        1.0
    } else if distance >= 8.0 {
        0.15
    } else {
        1.0 - 0.12 * (distance - 1.5)
    };

    let damped_fidelity = (baseline_intent * damping_factor).clamp(0.0, 0.999);

    // 3. Evaluate operational guard constraints (Fails if drifting entirely off structural limits)
    if distance >= 8.0 {
        return GuardedOutput {
            allowed: false,
            fidelity: damped_fidelity,
            neutralized_reason: CString::new("Critical variance: state out of bounds (distance > 8.0)").unwrap().into_raw(),
            derived_metric: std::ptr::null_mut(),
        };
    }

    // Allocate heap-allocated tracking space for the telemetry substrate
    let derived_alloc = Box::new(DerivedMetric {
        optimized_resonance: distance, // track the active drift offset safely
        lifecycle_epoch: m.timestamp + 1,
    });

    GuardedOutput {
        allowed: true,
        fidelity: damped_fidelity,
        neutralized_reason: std::ptr::null(),
        derived_metric: Box::into_raw(derived_alloc),
    }
}

#[no_mangle]
pub extern "C" fn free_guarded_output(output: GuardedOutput) {
    if !output.neutralized_reason.is_null() {
        unsafe { let _ = CString::from_raw(output.neutralized_reason as *mut c_char); }
    }
    if !output.derived_metric.is_null() {
        unsafe { let _ = Box::from_raw(output.derived_metric); }
    }
}
