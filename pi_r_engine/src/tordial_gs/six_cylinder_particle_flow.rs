// pi_r_engine/src/tordial_gs/six_cylinder_particle_flow.rs
use super::six_cylinder_boundary::{SystemState, FaceGeometry};
use std::f64::consts::PI;

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Phase {
    Intake,
    Transit,
    Exhaust,
    Return,
}

impl Phase {
    pub fn name(&self) -> &'static str {
        match self {
            Phase::Intake => "INTAKE",
            Phase::Transit => "TRANSIT",
            Phase::Exhaust => "EXHAUST",
            Phase::Return => "RETURN",
        }
    }
}

#[derive(Clone, Debug)]
pub struct Particle6D {
    pub x: f64, pub y: f64, pub z: f64,
    pub w: f64, pub v: f64, pub u: f64,
    pub dx: f64, pub dy: f64, pub dz: f64,
    pub dw: f64, pub dv: f64, pub du: f64,
    pub phase: Phase,
    pub life: u32,
    pub max_life: u32,
}

impl Particle6D {
    pub fn new(radius: f64) -> Self {
        // Simple uniform spawn on belt (matching your Python _spawn)
        let theta = rand::random::<f64>() * 2.0 * PI;
        let r = radius * (0.6 + 0.38 * rand::random::<f64>());
        Self {
            x: r * theta.cos(),
            y: r * theta.sin(),
            z: (rand::random::<f64>() - 0.5) * radius * 1.2,
            w: (rand::random::<f64>() - 0.5) * 3.0,
            v: (rand::random::<f64>() - 0.5) * 3.0,
            u: (rand::random::<f64>() - 0.5) * 3.0,
            dx: 0.0, dy: 0.0, dz: 0.0,
            dw: 0.0, dv: 0.0, du: 0.0,
            phase: Phase::Intake,
            life: 0,
            max_life: 220 + (rand::random::<u32>() % 120),
        }
    }
}

pub struct ParticleFlowEngine6D {
    pub particles: Vec<Particle6D>,
    count: usize,
}

impl ParticleFlowEngine6D {
    pub fn new(count: usize) -> Self {
        Self { particles: Vec::with_capacity(count), count }
    }

    pub fn step(&mut self, state: &SystemState, dt: f64) {
        let throat = state.core.throat * 0.5;
        let belt_r = state.belt.radius;

        // Respawn if needed
        while self.particles.len() < self.count {
            self.particles.push(Particle6D::new(belt_r));
        }

        let mut live = Vec::with_capacity(self.particles.len());

        for mut p in self.particles.drain(..) {
            p.life += 1;
            if p.life > p.max_life {
                live.push(Particle6D::new(belt_r));
                continue;
            }

            let r = (p.x * p.x + p.y * p.y).sqrt();
            let mut ax = 0.0; let mut ay = 0.0; let mut az = 0.0;
            let mut aw = 0.0; let mut av = 0.0; let mut au = 0.0;

            match p.phase {
                Phase::Intake => {
                    let tf = throat / (r + 1e-9);
                    ax = -1.5 * (p.x / belt_r) * tf;
                    ay = -1.5 * (p.y / belt_r) * tf;
                    az = -0.5 * p.z;
                    aw = 0.3 * state.spin;
                    if r < throat * 1.1 { p.phase = Phase::Transit; }
                }
                Phase::Transit => {
                    ax = -1.0 * p.y * state.spin * super::GEAR_SHIFT;
                    ay =  1.0 * p.x * state.spin * super::GEAR_SHIFT;
                    az =  0.1 * (p.w - p.v);
                    aw = (super::GEAR_SHIFT - p.w) * 0.5;
                    av = (state.temp - p.v) * 0.5;
                    if r > belt_r * 0.75 { p.phase = Phase::Exhaust; }
                }
                Phase::Exhaust => {
                    ax = 2.0 * (p.x / (r + 1e-9)) * super::SHADOW;
                    ay = 2.0 * (p.y / (r + 1e-9)) * super::SHADOW;
                    az = 0.8 * p.z * state.pressure;
                    if r > belt_r * 0.95 || p.z.abs() > belt_r * 0.6 {
                        p.phase = Phase::Return;
                    }
                }
                Phase::Return => {
                    let inv_p = 1.0 / (state.pressure + 1e-9);
                    ax = -2.5 * p.x * inv_p;
                    ay = -2.5 * p.y * inv_p;
                    az = -1.5 * p.z;
                    p.dw *= 0.1; p.dv *= 0.1; p.du *= 0.1;
                    if r < throat * 1.4 { p.phase = Phase::Intake; }
                }
            }

            p.dx += ax * dt; p.dy += ay * dt; p.dz += az * dt;
            p.dw += aw * dt; p.dv += av * dt; p.du += au * dt;

            let drag = (1.0 - 0.04 * state.pressure).max(0.5);
            p.dx *= drag; p.dy *= drag; p.dz *= drag;
            p.dw *= drag; p.dv *= drag; p.du *= drag;

            p.x += p.dx; p.y += p.dy; p.z += p.dz;
            p.w += p.dw; p.v += p.dv; p.u += p.du;

            live.push(p);
        }
        self.particles = live;
    }

    pub fn phase_counts(&self) -> [usize; 4] {
        let mut counts = [0usize; 4];
        for p in &self.particles {
            counts[p.phase as usize] += 1;
        }
        counts
    }
}