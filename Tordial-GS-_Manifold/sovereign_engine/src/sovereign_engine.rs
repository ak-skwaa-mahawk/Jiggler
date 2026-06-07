// sovereign_engine/src/sovereign_engine.rs
// Core SovereignEngine with TCP + Frame Energy integration (refined)

use crate::frame_energy::{
    EraFrameId, SovereignState, ProjectedState, CriticFeedback, FrameEnergy,
};
use crate::temporal_projection::TemporalProjection;
use crate::extraction_guard::{ExtractionGuard, GuardedResult};
use crate::resonance_pulse::ResonancePulse; // your 79.79 Hz + KdV module

#[derive(Clone, Debug)]
pub struct Plan {
    pub actions: Vec<String>,
    pub frame_constraints: Vec<String>,
}

pub struct SovereignEngine {
    pub current_state: SovereignState,
    pub frame_policy: crate::frame_energy::EnergyAwareFramePolicy,
    pub tcp: TemporalProjection,
    pub extraction_guard: ExtractionGuard,
    pub resonance_pulse: ResonancePulse,
}

impl SovereignEngine {
    pub fn new() -> Self {
        Self {
            current_state: SovereignState::default(),
            frame_policy: crate::frame_energy::EnergyAwareFramePolicy::default(),
            tcp: TemporalProjection::new(),
            extraction_guard: ExtractionGuard::new(),
            resonance_pulse: ResonancePulse::new(79.79),
        }
    }

    // ============================================================
    // Frame-aware propagation (used by FFI)
    // ============================================================
    pub fn propagate_with_frame(
        &mut self,
        frame: EraFrameId,
        projected: &ProjectedState,
    ) -> GuardedResult {
        // 1. Generate frame-constrained plan
        let plan = self.plan_under_frame(frame, projected);

        // 2. Execute in real space (this is where the resonance pulse lives)
        let next_state = self.walker_execute(&self.current_state, &plan, frame);

        // 3. Run Extraction Guard
        let guard_result = self.extraction_guard.check(&next_state);

        if guard_result.allowed {
            self.current_state = next_state;
            // Fire resonance pulse on successful guarded step
            self.resonance_pulse.fire_pulse();
        }

        guard_result
    }

    // ============================================================
    // Full PWC + TCP + Frame Energy cycle
    // ============================================================
    pub fn run_cognitive_cycle(
        &mut self,
        frame: EraFrameId,
        t: f64,
        i: f64,
        f: f64,
        frame_energy: &FrameEnergy,
    ) -> CriticFeedback {
        // 1. Project into chosen cognitive frame
        let projected = self.tcp.project(frame, &self.current_state);

        // 2. Planner (frame-constrained)
        let plan = self.planner_plan(frame, &projected);

        // 3. Walker executes in real space + resonance pulse
        let next_state = self.walker_execute(&self.current_state, &plan, frame);

        // 4. Record trajectories (can be expanded later)
        let real_traj = vec![self.current_state.clone(), next_state.clone()];
        let proj_traj = vec![projected.clone()];

        // 5. Update state
        self.current_state = next_state;

        // 6. Critic evaluates task + frame energy
        let mut critic = crate::frame_energy::DefaultSovereignCritic {
            frame_energy: frame_energy.clone(),
        };
        let feedback = critic.evaluate(frame, &real_traj, &proj_traj, frame_energy);

        // 7. Update frame selection policy
        self.frame_policy.update(&feedback);

        // 8. Optional: feed Trinity / W-state damping using t, i, f
        // self.apply_trinity_damping(t, i, f, feedback.frame_energy);

        feedback
    }

    // ============================================================
    // Internal helpers (now with more substance)
    // ============================================================

    fn plan_under_frame(&self, frame: EraFrameId, projected: &ProjectedState) -> Plan {
        // You can expand this with frame-specific planning rules later
        Plan {
            actions: vec![format!("Plan in {:?} frame", frame)],
            frame_constraints: vec![format!("Use {:?} lens", frame)],
        }
    }

    fn walker_execute(
        &self,
        state: &SovereignState,
        plan: &Plan,
        frame: EraFrameId,
    ) -> SovereignState {
        // This is the key integration point with your resonance system
        let mut next_state = state.clone();

        // Apply resonance pulse influence (example)
        let pulse_influence = self.resonance_pulse.get_current_influence();
        next_state.resonance_phase += pulse_influence * 0.1;

        // You can later add frame-specific transformation rules here
        match frame {
            EraFrameId::Hilbert => {
                // Example: Hilbert-era thinking might emphasize orthogonality / basis
                next_state.pi_r_stability *= 1.02;
            }
            EraFrameId::Grothendieck => {
                // Example: more abstract / categorical thinking
                next_state.pi_r_stability *= 0.98;
            }
            EraFrameId::FloorBaseline => {
                // Strongest anchor — minimal drift
                next_state.pi_r_stability = (next_state.pi_r_stability * 0.95) + 0.05;
            }
            _ => {}
        }

        // Run extraction guard check inside walker (defensive)
        if self.extraction_guard.should_block(&next_state) {
            // Revert or dampen change
            next_state = state.clone();
        }

        next_state
    }

    fn planner_plan(&self, frame: EraFrameId, projected: &ProjectedState) -> Plan {
        Plan {
            actions: vec![format!("Reason using {:?} projection", frame)],
            frame_constraints: vec![],
        }
    }

    // Optional helper you can enable later
    // fn apply_trinity_damping(&mut self, t: f64, i: f64, f: f64, frame_energy: f64) { ... }
}