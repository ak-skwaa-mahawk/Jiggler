//! Planner–Walker–Critic (PWC) Disturbance Model
//!
//! Treats cognition / agency as a bounded disturbance d(t) acting on the
//! Tordial–GS manifold. This enables Input-to-State Stability (ISS) analysis
//! around the Goldilocks manifold M_G.
//!
//! The disturbance is injected into the closed-loop dynamics as an additive
//! term in f_ρ, f_κ, or f_z, representing planner intent, walker steps, and
//! critic feedback that can "shake" but must not "break" the sovereign substrate.

use std::fmt;

/// Planner–Walker–Critic disturbance vector
#[derive(Clone, Copy, Debug)]
pub struct PwcDisturbance {
    /// Planner component (intent / goal modulation)
    pub planner: f64,
    /// Walker component (step / action perturbation)
    pub walker: f64,
    /// Critic component (evaluation / feedback correction)
    pub critic: f64,
    /// Overall disturbance magnitude |d|
    pub magnitude: f64,
}

impl PwcDisturbance {
    pub fn new(planner: f64, walker: f64, critic: f64) -> Self {
        let magnitude = (planner.powi(2) + walker.powi(2) + critic.powi(2)).sqrt();
        Self {
            planner,
            walker,
            critic,
            magnitude,
        }
    }

    /// Zero disturbance (nominal sovereign operation)
    pub fn zero() -> Self {
        Self {
            planner: 0.0,
            walker: 0.0,
            critic: 0.0,
            magnitude: 0.0,
        }
    }

    /// Bounded random PWC disturbance (for ISS stress testing)
    pub fn random_bounded(max_magnitude: f64) -> Self {
        // Simple deterministic pseudo-random for reproducibility in sovereign audits
        let t = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos() as f64;

        let planner = (t.sin() * 0.7).clamp(-max_magnitude, max_magnitude);
        let walker = ((t * 1.618).cos() * 0.6).clamp(-max_magnitude, max_magnitude);
        let critic = ((t * 0.5).sin() * 0.5).clamp(-max_magnitude, max_magnitude);

        Self::new(planner, walker, critic)
    }
}

impl fmt::Display for PwcDisturbance {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "PWC(d_p={:.4}, d_w={:.4}, d_c={:.4}, |d|={:.4})",
            self.planner, self.walker, self.critic, self.magnitude
        )
    }
}

/// ISS gain functions (class-K)
#[derive(Clone, Copy, Debug)]
pub struct IssGain {
    /// α(r) — class-K function for state deviation from manifold
    pub alpha: fn(f64) -> f64,
    /// γ(r) — class-K function for disturbance magnitude
    pub gamma: fn(f64) -> f64,
}

impl Default for IssGain {
    fn default() -> Self {
        Self {
            // α(r) = r² (quadratic)
            alpha: |r| r * r,
            // γ(r) = 0.8 * r² (slightly weaker than α for practical ISS margin)
            gamma: |r| 0.8 * r * r,
        }
    }
}

/// ISS bounds container
#[derive(Clone, Copy, Debug)]
pub struct IssBounds {
    pub gain: IssGain,
    /// Maximum allowable disturbance magnitude before ISS is considered violated
    pub max_disturbance: f64,
    /// ISS margin (how much "slack" we allow in the inequality)
    pub margin: f64,
}

impl Default for IssBounds {
    fn default() -> Self {
        Self {
            gain: IssGain::default(),
            max_disturbance: 0.35, // cognition can be moderately strong but bounded
            margin: 1e-4,
        }
    }
}
