use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use crate::core::substrate_bus::{PySubstrateMeshBus, RecordType};
use std::collections::{HashSet, HashMap};
use std::fs::File;
use std::io::Read;
use std::path::Path;

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "SCREAMING_SNAKE_CASE")]
#[pyclass(rename_all = "SCREAMING_SNAKE_CASE")]
pub enum DecisionStatus {
    Resting,
    SovereignClauseEmit,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct DecisionRecord {
    #[pyo3(get)]
    pub timestamp: u64,
    #[pyo3(get)]
    pub initial_distance: f64,
    #[pyo3(get)]
    pub trial_distance: f64,
    #[pyo3(get)]
    pub utility_gain: f64,
    #[pyo3(get)]
    pub status: DecisionStatus,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass(get_all, set_all)]
pub struct WaveTrajectoryPoint {
    pub step: u64,
    pub t: f64,
    pub position: f64,
    pub velocity: f64,
    pub resonance_hz: f64,
    pub sovereign_alpha: f64,
    pub damping: f64,
    pub authorized: bool,
    pub provenance_hash: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass(get_all, set_all)]
pub struct LiveWaveState {
    pub step: u64,
    pub simulated_time: f64,
    pub position: f64,
    pub velocity: f64,
    pub resonance_hz: f64,
    pub damping: f64,
    pub sovereign_alpha: f64,
    pub kinetic_energy: f64,
    pub potential_energy: f64,
    pub total_energy: f64,
    pub operator_authorized: bool,
    pub manifold_coupling_term: f64,
    pub coherence_index: f64,
    pub provenance_hash: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass(get_all, set_all)]
pub struct LiveMacroSnapshot {
    pub step: u64,
    pub simulated_time: f64,
    pub global_phase_x: f64,
    pub global_phase_y: f64,
    pub macro_forcing_ceiling: f64,
    pub phase_relaxation_rate: f64,
    pub attractor_strength: f64,
    pub effective_lyapunov_exponent: f64,
    pub manifold_coupling_term: f64,
    pub resonance_hz: f64,
    pub coherence_index: f64,
    pub active_semantic_locks: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass(get_all, set_all)]
pub struct SemanticResonanceEvent {
    pub step: u64,
    pub timestamp: u64,
    pub lane: String,
    pub variance: f64,
    pub status: String, 
    pub locked_actor_ids: Vec<u64>,
    pub coupling_boost_applied: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass(get_all, set_all)]
pub struct CoherenceReport {
    pub energy_drift: f64,
    pub frequency_detuning: f64,
    pub coherence_index: f64,
    pub structural_lock_active: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass(get_all, set_all)]
pub struct ResonanceStabilityReport {
    pub step: u64,
    pub timestamp: u64,
    pub total_system_energy: f64,
    pub rolling_energy_variance: f64,
    pub status_code: String,
}

#[pyclass(get_all, set_all)]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WaveActor {
    pub actor_id: u64,
    pub position: f64,
    pub velocity: f64,
    pub sovereign_alpha: f64,
    pub glyph_resonance_hz: f64,
    pub damping: f64,
    pub operator_authorized: bool,
    pub semantic_layer: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass(get_all, set_all)]
pub struct PortableActorState {
    pub actor_id: u64,
    pub position: f64,
    pub velocity: f64,
    pub glyph_resonance_hz: f64,
    pub coherence_index: f64,
    pub authorized: bool,
    pub auth_source_hash: String,
    pub authorized_at: u64,
    pub lineage_root: String,
    pub issuer_actor: u64,
    pub semantic_layer: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass(get_all, set_all)]
pub struct PortableManifoldBundle {
    pub version: u32,
    pub exported_at: u64,
    pub last_macro_snapshot: LiveMacroSnapshot,
    pub glyph_resonance_hz: f64,
    pub metadata_tag: String,
    pub active_ensemble: Vec<PortableActorState>,
    pub active_semantic_locks: Vec<String>,
}

#[pyclass(get_all, set_all)]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TordialCoupledState {
    pub global_phase_x: f64,
    pub global_phase_y: f64,
    pub macro_forcing_ceiling: f64,
    pub phase_relaxation_rate: f64,
    pub attractor_strength: f64,
    pub effective_lyapunov_exponent: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct TrustCertificate {
    pub auth_hash: String,
    pub timestamp: u64,
    pub root_label: String,
    pub issuer: u64,
}

#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AuthorizedActorRegistry {
    #[pyo3(get)]
    pub allowed_ids: HashSet<u64>,
    #[serde(skip)]
    pub trust_metadata: HashMap<u64, TrustCertificate>,
}

#[pyclass]
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DinjjiEnsemble {
    #[pyo3(get)]
    pub actors: Vec<WaveActor>,
    #[pyo3(get)]
    pub mean_coherence: f64,
    #[pyo3(get)]
    pub combined_coupling_term: f64,
    #[pyo3(get)]
    pub registry: AuthorizedActorRegistry,
    #[serde(skip)]
    pub active_cluster_locks: HashSet<String>,
    pub baseline_total_energy: f64,
}

#[pymethods]
impl AuthorizedActorRegistry {
    #[new]
    pub fn new() -> Self {
        let mut allowed = HashSet::new();
        allowed.insert(101);
        allowed.insert(102);
        
        let mut trust_metadata = HashMap::new();
        trust_metadata.insert(101, TrustCertificate {
            auth_hash: String::from("ROOT_STATIC_ALPHA"),
            timestamp: 1785000000,
            root_label: String::from("Esias Joseph 1906 Root"),
            issuer: 777,
        });
        trust_metadata.insert(102, TrustCertificate {
            auth_hash: String::from("ROOT_STATIC_BETA"),
            timestamp: 1785000000,
            root_label: String::from("Esias Joseph 1906 Root"),
            issuer: 777,
        });

        AuthorizedActorRegistry { allowed_ids: allowed, trust_metadata }
    }

    pub fn load_from_handshake_ledger(&mut self, handshake_file_path: String) -> PyResult<usize> {
        let path = Path::new(&handshake_file_path);
        if !path.exists() {
            return Ok(0);
        }

        let mut file = File::open(path).map_err(|e| pyo3::exceptions::PyIOError::new_err(format!("{}", e)))?;
        let mut content = String::new();
        file.read_to_string(&mut content).unwrap_or_default();
        
        let mut enrollment_count = 0;
        if let Ok(blocks_data) = serde_json::from_str::<serde_json::Value>(&content) {
            if let Some(arr) = blocks_data.as_array() {
                for block in arr {
                    let block_hash = block.get("hash").and_then(|h| h.as_str()).unwrap_or("UNKNOWN_HASH").to_string();
                    let block_time = block.get("timestamp").and_then(|t| t.as_u64()).unwrap_or(0);
                    
                    if let Some(payload) = block.get("payload").or_else(|| block.get("PAYLOAD")) {
                        let record_type = payload.get("record_type")
                            .or_else(|| payload.get("RECORD_TYPE"))
                            .and_then(|r| r.as_str())
                            .unwrap_or("");
                        
                        if record_type.contains("HANDSHAKE") || record_type.contains("Verification") {
                            if let Some(raw_fallback) = payload.get("fallback_raw_data")
                                .or_else(|| payload.get("FALLBACK_RAW_DATA"))
                                .and_then(|f| f.as_str()) 
                            {
                                if let Ok(val_obj) = serde_json::from_str::<serde_json::Value>(raw_fallback) {
                                    if let Some(subject_id) = val_obj.get("SUBJECT_ACTOR")
                                        .or_else(|| val_obj.get("subject_actor"))
                                        .and_then(|s| s.as_u64()) 
                                    {
                                        self.allowed_ids.insert(subject_id);
                                        self.trust_metadata.insert(subject_id, TrustCertificate {
                                            auth_hash: block_hash.clone(),
                                            timestamp: block_time,
                                            root_label: String::from("Esias Joseph 1906 Dynamic"),
                                            issuer: 777,
                                        });
                                        enrollment_count += 1;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        Ok(enrollment_count)
    }

    pub fn is_id_authorized(&self, actor_id: u64) -> bool {
        self.allowed_ids.contains(&actor_id)
    }

    pub fn get_metadata_hash(&self, actor_id: u64) -> String {
        self.trust_metadata.get(&actor_id)
            .map(|c| c.auth_hash.clone())
            .unwrap_or_else(|| String::from("UNVERIFIED_SOURCE"))
    }

    pub fn get_metadata_timestamp(&self, actor_id: u64) -> u64 {
        self.trust_metadata.get(&actor_id).map(|c| c.timestamp).unwrap_or(0)
    }

    pub fn get_metadata_root(&self, actor_id: u64) -> String {
        self.trust_metadata.get(&actor_id)
            .map(|c| c.root_label.clone())
            .unwrap_or_else(|| String::from("NONE"))
    }
}

#[pymethods]
impl WaveActor {
    #[new]
    pub fn new(actor_id: u64) -> Self {
        WaveActor {
            actor_id,
            position: 0.0,
            velocity: 0.0,
            sovereign_alpha: 1.5,
            glyph_resonance_hz: 7.9083,
            damping: 0.15,
            operator_authorized: false,
            semantic_layer: String::from("Dinjji Zhuu Kwaa"),
        }
    }

    pub fn rehydrate_from_bus(&mut self, bus: &PySubstrateMeshBus) {
        let (alpha, _, _, target_damping, authorized) = bus.compute_sovereign_multipliers();
        self.sovereign_alpha = alpha;
        self.damping = target_damping;
        self.operator_authorized = authorized;

        let chain = bus.chain.lock().unwrap();
        for block in chain.iter() {
            if let Some(ref glyph) = block.payload.gwichin_glyph {
                if glyph.resonance_hz > 0.0 {
                    self.glyph_resonance_hz = glyph.resonance_hz;
                    self.semantic_layer = glyph.semantic_layer.clone();
                    break;
                }
            }
        }
    }

    pub fn compute_coherence_index(&self) -> f64 {
        if self.glyph_resonance_hz <= 0.0 { return 0.0; }
        let ke = 0.5 * self.velocity * self.velocity;
        let normalized_ke = (ke / (self.sovereign_alpha + 1e-9)).clamp(0.0, 2.0);
        (1.0 - (normalized_ke - 0.5).abs()).clamp(0.0, 1.0)
    }

    pub fn step_wave_actor_bidirectional(&mut self, dt: f64, t: f64, global_x: f64, global_y: f64) -> (f64, f64) {
        let omega = self.glyph_resonance_hz * 2.0 * std::f64::consts::PI;
        let f_drive = self.sovereign_alpha * (omega * t).cos();
        let f_restore = -self.position / (1.0 + self.position * self.position);
        
        let macro_displacement = global_x * global_x + global_y * global_y;
        let dynamic_damping = self.damping * (1.0 + macro_displacement.tanh() * 0.1);
        let f_damp = -dynamic_damping * self.velocity;

        let acceleration = f_drive + f_restore + f_damp;
        self.velocity += acceleration * dt;
        self.position += self.velocity * dt;

        (self.position, self.velocity)
    }

    pub fn step_wave_actor(&mut self, dt: f64, t: f64) -> (f64, f64) {
        self.step_wave_actor_bidirectional(dt, t, 0.0, 0.0)
    }

    pub fn compute_energy_state(&self) -> (f64, f64, f64) {
        let kinetic = 0.5 * self.velocity * self.velocity;
        let potential = 0.5 * (1.0 + self.position * self.position).ln();
        let total = kinetic + potential;
        (kinetic, potential, total)
    }

    pub fn compute_manifold_coupling(&self) -> f64 {
        if !self.operator_authorized { return 1.0; }
        1.0 + (self.position * self.velocity.sin())
    }

    pub fn get_live_state(&self, step: u64, t: f64) -> LiveWaveState {
        let (ke, pe, te) = self.compute_energy_state();
        let coupling = self.compute_manifold_coupling();
        let coherence = self.compute_coherence_index();
        LiveWaveState {
            step,
            simulated_time: t,
            position: self.position,
            velocity: self.velocity,
            resonance_hz: self.glyph_resonance_hz,
            damping: self.damping,
            sovereign_alpha: self.sovereign_alpha,
            kinetic_energy: ke,
            potential_energy: pe,
            total_energy: te,
            operator_authorized: self.operator_authorized,
            manifold_coupling_term: coupling,
            coherence_index: coherence,
            provenance_hash: String::from("ROOT_STATIC_ALPHA"),
        }
    }

    pub fn get_current_metrics(&self) -> (f64, f64, f64, f64, bool) {
        (self.position, self.velocity, self.glyph_resonance_hz, self.damping, self.operator_authorized)
    }

    pub fn export_telemetry_point(&self, step: u64, t: f64) -> WaveTrajectoryPoint {
        WaveTrajectoryPoint {
            step,
            t,
            position: self.position,
            velocity: self.velocity,
            resonance_hz: self.glyph_resonance_hz,
            sovereign_alpha: self.sovereign_alpha,
            damping: self.damping,
            authorized: self.operator_authorized,
            provenance_hash: String::from("ROOT_STATIC_ALPHA"),
        }
    }

    pub fn export_telemetry_string_with_hash(&self, step: u64, t: f64, prov_hash: &str) -> String {
        let (ke, pe, te) = self.compute_energy_state();
        format!(
            "WAVE_TRAJECTORY|step={}|actor_id={}|resonance_hz={:.4}|pos={:.6}|vel={:.6}|t={:.4}|authorized={}|damping={:.4}|ke={:.6}|pe={:.6}|energy_total={:.6}|provenance={}|semantic_layer={}",
            step, self.actor_id, self.glyph_resonance_hz, self.position, self.velocity, t, self.operator_authorized, self.damping, ke, pe, te, prov_hash, self.semantic_layer
        )
    }

    pub fn export_telemetry_string(&self, step: u64, t: f64) -> String {
        self.export_telemetry_string_with_hash(step, t, "ROOT_STATIC_ALPHA")
    }
}

#[pymethods]
impl DinjjiEnsemble {
    #[new]
    pub fn new() -> Self {
        DinjjiEnsemble {
            actors: Vec::new(),
            mean_coherence: 1.0,
            combined_coupling_term: 1.0,
            registry: AuthorizedActorRegistry::new(),
            active_cluster_locks: HashSet::new(),
            baseline_total_energy: 0.0,
        }
    }

    pub fn register_actor(&mut self, actor: WaveActor) {
        self.actors.push(actor);
    }

    pub fn clear_ensemble(&mut self) {
        self.actors.clear();
    }

    pub fn get_actor_count(&self) -> usize {
        self.actors.len()
    }

    pub fn get_active_locks_list(&self) -> Vec<String> {
        self.active_cluster_locks.iter().cloned().collect()
    }

    pub fn ingest_handoff_bundle_string(&mut self, bundle_json: String) -> PyResult<bool> {
        if let Ok(bundle) = serde_json::from_str::<PortableManifoldBundle>(&bundle_json) {
            self.actors.clear();
            self.active_cluster_locks.clear();
            
            for lock in bundle.active_semantic_locks {
                self.active_cluster_locks.insert(lock);
            }
            
            for p_actor in bundle.active_ensemble {
                let mut actor = WaveActor::new(p_actor.actor_id);
                actor.position = p_actor.position;
                actor.velocity = p_actor.velocity;
                actor.glyph_resonance_hz = p_actor.glyph_resonance_hz;
                actor.operator_authorized = p_actor.authorized;
                actor.semantic_layer = p_actor.semantic_layer;
                self.actors.push(actor);
            }
            return Ok(true);
        }
        Ok(false)
    }

    pub fn execute_energy_conservation_audit(&mut self, step: u64) -> PyResult<ResonanceStabilityReport> {
        let mut current_total = 0.0;
        let mut authorized_count = 0;
        
        for actor in &self.actors {
            if self.registry.is_id_authorized(actor.actor_id) || actor.operator_authorized {
                let (_, _, actor_total) = actor.compute_energy_state();
                current_total += actor_total;
                authorized_count += 1;
            }
        }
        
        if self.baseline_total_energy <= 0.0 && authorized_count > 0 {
            self.baseline_total_energy = current_total;
        }
        
        let drift_variance = (current_total - self.baseline_total_energy).abs();
        let status_code = if drift_variance > 0.15 {
            String::from("LONG_TERM_DRIFT_WARN")
        } else {
            String::from("STABLE_RESONANT_FIELD")
        };
        
        let sys_time = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);
            
        Ok(ResonanceStabilityReport {
            step,
            timestamp: sys_time,
            total_system_energy: current_total,
            rolling_energy_variance: drift_variance,
            status_code,
        })
    }

    pub fn sync_registry_and_detect_mutations(&mut self, path: String) -> PyResult<Vec<String>> {
        let old_ids = self.registry.allowed_ids.clone();
        self.registry.load_from_handshake_ledger(path)?;
        let mut changes = Vec::new();

        for id in &self.registry.allowed_ids {
            if !old_ids.contains(id) {
                let p_hash = self.registry.get_metadata_hash(*id);
                changes.push(format!("REGISTRY_MUTATION|actor_id={}|action=ENROLLED|provenance={}", id, p_hash));
            }
        }
        Ok(changes)
    }

    pub fn sync_authorized_nodes(&mut self, path: String) -> PyResult<usize> {
        self.registry.load_from_handshake_ledger(path)
    }

    pub fn monitor_semantic_cluster_guard_rails(&mut self, step: u64) -> PyResult<Vec<SemanticResonanceEvent>> {
        let mut event_objects = Vec::new();
        let mut lane_positions: HashMap<String, Vec<(u64, f64)>> = HashMap::new();

        for actor in &self.actors {
            if self.registry.is_id_authorized(actor.actor_id) || actor.operator_authorized {
                lane_positions.entry(actor.semantic_layer.clone())
                    .or_insert_with(Vec::new)
                    .push((actor.actor_id, actor.position));
            }
        }

        let sys_time = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .map(|d| d.as_secs())
            .unwrap_or(0);

        for (lane, elements) in lane_positions {
            if elements.len() >= 2 {
                let count = elements.len() as f64;
                let positions: Vec<f64> = elements.iter().map(|e| e.1).collect();
                let actor_ids: Vec<u64> = elements.iter().map(|e| e.0).collect();
                
                let mean: f64 = positions.iter().sum::<f64>() / count;
                let variance: f64 = positions.iter().map(|p| (p - mean).powi(2)).sum::<f64>() / count;
                
                let boost_applied = (elements.len() - 1) as f64 * 0.25;

                if variance < 0.005 {
                    if !self.active_cluster_locks.contains(&lane) {
                        self.active_cluster_locks.insert(lane.clone());
                        event_objects.push(SemanticResonanceEvent {
                            step,
                            timestamp: sys_time,
                            lane: lane.clone(),
                            variance,
                            status: String::from("RESONANCE_LOCK_ACHIEVED"),
                            locked_actor_ids: actor_ids,
                            coupling_boost_applied: boost_applied,
                        });
                    }
                } else {
                    if self.active_cluster_locks.contains(&lane) {
                        self.active_cluster_locks.remove(&lane);
                        event_objects.push(SemanticResonanceEvent {
                            step,
                            timestamp: sys_time,
                            lane: lane.clone(),
                            variance,
                            status: String::from("ENSEMBLE_SEMANTIC_DRIFT"),
                            locked_actor_ids: actor_ids,
                            coupling_boost_applied: 0.0,
                        });
                    }
                }
            }
        }
        Ok(event_objects)
    }

    // Fixed: Wires Phonetic engine inputs dynamically into the cross-coupling multiplier calculations
    pub fn step_ensemble_with_phonetic_modulator(&mut self, dt: f64, t: f64, global_x: f64, global_y: f64, phonetic_hz: f64) -> (f64, f64) {
        if self.actors.is_empty() {
            return (1.0, 1.0);
        }

        let mut total_coupling = 0.0;
        let mut total_coherence = 0.0;
        let mut authoritative_node_count = 0.0;

        let mut active_semantics: Vec<(usize, String, bool)> = Vec::new();
        for (i, actor) in self.actors.iter().enumerate() {
            let verified = self.registry.is_id_authorized(actor.actor_id) || actor.operator_authorized;
            active_semantics.push((i, actor.semantic_layer.clone(), verified));
        }

        // Apply phonetic shift as a secondary tuning modulator across actors sharing identical lanes
        let phonetic_detuning_modifier = (phonetic_hz - 7.9083).abs().tanh() * 0.15;

        for i in 0..self.actors.len() {
            let (idx, ref layer_tag, is_authed) = active_semantics[i];
            
            let actor = &mut self.actors[idx];
            actor.step_wave_actor_bidirectional(dt, t, global_x, global_y);
            
            if is_authed {
                let mut coupling_scalar = actor.compute_manifold_coupling();
                
                for j in 0..active_semantics.len() {
                    if i != j && active_semantics[j].2 && &active_semantics[j].1 == layer_tag {
                        // Dynamic phonetic weight coupling scaling factor adjustment
                        coupling_scalar += 0.25 - phonetic_detuning_modifier; 
                    }
                }

                total_coupling += coupling_scalar;
                total_coherence += actor.compute_coherence_index();
                authoritative_node_count += 1.0;
            }
        }

        let divisors = if authoritative_node_count > 0.0 { authoritative_node_count } else { 1.0 };
        self.combined_coupling_term = total_coupling / divisors;
        self.mean_coherence = total_coherence / divisors;

        (self.combined_coupling_term, self.mean_coherence)
    }

    pub fn step_ensemble(&mut self, dt: f64, t: f64, global_x: f64, global_y: f64) -> (f64, f64) {
        self.step_ensemble_with_phonetic_modulator(dt, t, global_x, global_y, 7.9083)
    }

    pub fn is_actor_index_authorized(&self, idx: usize) -> PyResult<bool> {
        if idx >= self.actors.len() {
            return Err(pyo3::exceptions::PyIndexError::new_err("Ensemble actor index out of range"));
        }
        let a = &self.actors[idx];
        Ok(self.registry.is_id_authorized(a.actor_id) || a.operator_authorized)
    }

    pub fn export_actor_telemetry_string(&self, idx: usize, step: u64, t: f64) -> PyResult<String> {
        if idx >= self.actors.len() {
            return Err(pyo3::exceptions::PyIndexError::new_err("Ensemble actor index out of range"));
        }
        let hash_str = self.registry.get_metadata_hash(self.actors[idx].actor_id);
        Ok(self.actors[idx].export_telemetry_string_with_hash(step, t, &hash_str))
    }

    pub fn get_actor_total_energy(&self, idx: usize) -> PyResult<f64> {
        if idx >= self.actors.len() {
            return Err(pyo3::exceptions::PyIndexError::new_err("Ensemble actor index out of range"));
        }
        let (_, _, total) = self.actors[idx].compute_energy_state();
        Ok(total)
    }

    pub fn get_actor_provenance_hash(&self, idx: usize) -> PyResult<String> {
        if idx >= self.actors.len() {
            return Err(pyo3::exceptions::PyIndexError::new_err("Ensemble actor index out of range"));
        }
        Ok(self.registry.get_metadata_hash(self.actors[idx].actor_id))
    }
}

#[pymethods]
impl TordialCoupledState {
    #[new]
    pub fn default() -> Self {
        TordialCoupledState {
            global_phase_x: 1.0,
            global_phase_y: 1.0,
            macro_forcing_ceiling: 1000.0,
            phase_relaxation_rate: 0.15,
            attractor_strength: 1.0,
            effective_lyapunov_exponent: 0.0,
        }
    }

    pub fn emit_macro_snapshot(&self, step: u64) -> LiveMacroSnapshot {
        LiveMacroSnapshot {
            step,
            simulated_time: 0.0,
            global_phase_x: self.global_phase_x,
            global_phase_y: self.global_phase_y,
            macro_forcing_ceiling: self.macro_forcing_ceiling,
            phase_relaxation_rate: self.phase_relaxation_rate,
            attractor_strength: self.attractor_strength,
            effective_lyapunov_exponent: self.effective_lyapunov_exponent,
            manifold_coupling_term: 1.0,
            resonance_hz: 7.9083,
            coherence_index: 1.0,
            active_semantic_locks: Vec::new(),
        }
    }

    pub fn ingest_macro_snapshot_bundle(&mut self, bundle_json: String) -> PyResult<bool> {
        if let Ok(bundle) = serde_json::from_str::<PortableManifoldBundle>(&bundle_json) {
            self.global_phase_x = bundle.last_macro_snapshot.global_phase_x;
            self.global_phase_y = bundle.last_macro_snapshot.global_phase_y;
            self.macro_forcing_ceiling = bundle.last_macro_snapshot.macro_forcing_ceiling;
            self.phase_relaxation_rate = bundle.last_macro_snapshot.phase_relaxation_rate;
            self.attractor_strength = bundle.last_macro_snapshot.attractor_strength;
            self.effective_lyapunov_exponent = bundle.last_macro_snapshot.effective_lyapunov_exponent;
            return Ok(true);
        }
        Ok(false)
    }

    pub fn to_snapshot(&self, step: u64, t: f64, coupling: f64, resonance: f64, coherence: f64, active_locks: Vec<String>) -> LiveMacroSnapshot {
        LiveMacroSnapshot {
            step,
            simulated_time: t,
            global_phase_x: self.global_phase_x,
            global_phase_y: self.global_phase_y,
            macro_forcing_ceiling: self.macro_forcing_ceiling,
            phase_relaxation_rate: self.phase_relaxation_rate,
            attractor_strength: self.attractor_strength,
            effective_lyapunov_exponent: self.effective_lyapunov_exponent,
            manifold_coupling_term: coupling,
            resonance_hz: resonance,
            coherence_index: coherence,
            active_semantic_locks: active_locks,
        }
    }

    pub fn rehydrate_from_proof_bus(&mut self, bus: &PySubstrateMeshBus) -> bool {
        let chain = bus.chain.lock().unwrap();
        
        for block in chain.iter().rev() {
            let raw_data = block.payload.fallback_raw_data.trim();
            if raw_data.is_empty() {
                continue;
            }

            let clean_json = if raw_data.starts_with("STRUCTURED_MACRO_JSON|") {
                &raw_data["STRUCTURED_MACRO_JSON|".len()..]
            } else {
                raw_data
            };

            if let Ok(v) = serde_json::from_str::<serde_json::Value>(clean_json) {
                let x_val = v.get("GLOBAL_PHASE_X")
                    .or_else(|| v.get("global_phase_x"))
                    .and_then(|x| x.as_f64());
                    
                let y_val = v.get("GLOBAL_PHASE_Y")
                    .or_else(|| v.get("global_phase_y"))
                    .and_then(|y| y.as_f64());

                if let (Some(x), Some(y)) = (x_val, y_val) {
                    self.global_phase_x = x;
                    self.global_phase_y = y;
                    
                    if let Some(mfc) = v.get("macro_forcing_ceiling").or_else(|| v.get("MACRO_FORCING_CEILING")).and_then(|m| m.as_f64()) {
                        self.macro_forcing_ceiling = mfc;
                    }
                    if let Some(prr) = v.get("phase_relaxation_rate").or_else(|| v.get("PHASE_RELAXATION_RATE")).and_then(|p| p.as_f64()) {
                        self.phase_relaxation_rate = prr;
                    }
                    if let Some(ats) = v.get("attractor_strength").or_else(|| v.get("ATTRACTOR_STRENGTH")).and_then(|a| a.as_f64()) {
                        self.attractor_strength = ats;
                    }
                    if let Some(ele) = v.get("effective_lyapunov_exponent").or_else(|| v.get("EFFECTIVE_LYAPUNOV_EXPONENT")).and_then(|l| l.as_f64()) {
                        self.effective_lyapunov_exponent = ele;
                    }
                    return true;
                }
            }
        }
        false
    }

    pub fn export_ensemble_bundle_string(&self, step: u64, resonance: f64, mean_coherence: f64, python_actors: Vec<WaveActor>, active_locks: Vec<String>) -> PyResult<String> {
        let mut rust_actors = Vec::new();
        let default_registry = AuthorizedActorRegistry::new();
        for a in python_actors {
            let is_authed = default_registry.is_id_authorized(a.actor_id) || a.operator_authorized;
            rust_actors.push(PortableActorState {
                actor_id: a.actor_id,
                position: a.position,
                velocity: a.velocity,
                glyph_resonance_hz: a.glyph_resonance_hz,
                coherence_index: a.compute_coherence_index(),
                authorized: is_authed,
                auth_source_hash: default_registry.get_metadata_hash(a.actor_id),
                authorized_at: default_registry.get_metadata_timestamp(a.actor_id),
                lineage_root: default_registry.get_metadata_root(a.actor_id),
                issuer_actor: 777,
                semantic_layer: a.semantic_layer.clone(),
            });
        }

        let bundle = PortableManifoldBundle {
            version: 2,
            exported_at: 1785000000, 
            last_macro_snapshot: self.to_snapshot(step, 0.0, 1.0, resonance, mean_coherence, active_locks.clone()),
            glyph_resonance_hz: resonance,
            metadata_tag: String::from("SOVEREIGN_OUT_OF_BAND_MATRIX_v2"),
            active_ensemble: rust_actors,
            active_semantic_locks: active_locks,
        };
        serde_json::to_string_pretty(&bundle)
            .map_err(|e| pyo3::exceptions::PyValueError::new_err(format!("Export failure: {}", e)))
    }

    pub fn evaluate_coherence_guard(&self, current_total_energy: f64, current_resonance_hz: f64) -> CoherenceReport {
        let baseline_energy = 0.5; 
        let energy_drift = (current_total_energy - baseline_energy).abs();
        let frequency_detuning = (current_resonance_hz - 7.9083).abs();
        
        let coherence_index = 1.0 / (1.0 + (energy_drift * 2.0) + (frequency_detuning * 5.0));
        let structural_lock_active = coherence_index < 0.25;

        CoherenceReport {
            energy_drift,
            frequency_detuning,
            coherence_index,
            structural_lock_active,
        }
    }

    pub fn apply_parametric_coupling(&mut self, coupling_term: f64, glyph_resonance_hz: f64) {
        self.macro_forcing_ceiling = 1000.0 * coupling_term;
        self.phase_relaxation_rate = 0.15 / (0.5 + 0.5 * coupling_term).max(0.01);
        let frequency_detuning = glyph_resonance_hz - 7.9083;
        self.attractor_strength = 1.0 - (frequency_detuning.tanh() * 0.05);
    }

    pub fn evolve_coupled_geometry(&mut self, dt: f64) {
        let dx = (self.global_phase_y - self.global_phase_x * self.phase_relaxation_rate) * self.attractor_strength * dt;
        let dy = (-self.global_phase_x + (self.macro_forcing_ceiling / 1000.0)) * self.attractor_strength * dt;

        self.global_phase_x += dx;
        self.global_phase_y += dy;

        self.effective_lyapunov_exponent = (dx.powi(2) + dy.powi(2)).sqrt().ln_or_zero();
    }
}

trait LnOrZero {
    fn ln_or_zero(self) -> f64;
}
impl LnOrZero for f64 {
    fn ln_or_zero(self) -> f64 {
        if self <= 0.0 { 0.0 } else { self.ln() }
    }
}
