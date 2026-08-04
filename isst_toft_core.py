#!/usr/bin/env python3
# isst_toft_core.py — Unified Nervous System Core (v1.7.0 Behavioral Routing Engine)
import os
import sys
import json
import re
import math
from datetime import datetime, timezone

class ResonanceStateCore:
    def __init__(self):
        self.base_dir = os.path.expanduser("~/Tordial-GS-_Manifold")
        self.ledger_path = os.path.join(self.base_dir, "state_ledger.json")
        self.trajectory_path = os.path.join(self.base_dir, "manifold_trajectories.jsonl")
        self.attractor_path = os.path.join(self.base_dir, "manifold_attractors.json")
        self.max_history = 5
        self.default_clamp = 7.8800
        self.sensitive_clamp = 7.8400
        self.recovery_threshold_base = 7.8500
        self.gamma = 0.5  # Resonance sensitivity decay coefficient
        self.max_attractors = 8
        self.decay_timeout_sec = 300
        self.merge_threshold_d = 0.25

    def calculate_variance_score(self, text: str) -> float:
        """Calculates phonetic resonance baseline matrix using string variance values."""
        if not text:
            return 0.0
        char_sum = sum(ord(c) for c in text)
        return round((char_sum % 100) / 100.0, 4)

    def synthesize_harmonics(self, text: str, base_hz: float) -> dict:
        """Decomposes the linguistic structure to synthesize harmonic sub-frequencies."""
        clean_text = text.lower()
        total_chars = len(clean_text) if len(clean_text) > 0 else 1
        
        vowels = len(re.findall(r'[aeiou]', clean_text))
        consonants = len(re.findall(r'[bcdfghjklmnpqrstvwxyz]', clean_text))
        spaces = len(re.findall(r'\s', clean_text))
        
        vowel_density = round(vowels / total_chars, 4)
        consonant_density = round(consonants / total_chars, 4)
        
        f2_multiplier = 1.5 + (vowel_density * 0.5)
        sub_divider = 2.0 - (consonant_density * 0.2)
        
        f2_harmonic = round(base_hz * f2_multiplier, 4)
        sub_harmonic = round(base_hz / sub_divider, 4)
        
        return {
            "phonetic_profile": {
                "length": len(text),
                "vowel_density": vowel_density,
                "consonant_density": consonant_density,
                "space_count": spaces
            },
            "frequency_synthesis": {
                "fundamental_f0_hz": base_hz,
                "second_harmonic_f2_hz": f2_harmonic,
                "sub_harmonic_f1_hz": sub_harmonic,
                "spectral_envelope_spread": round(f2_harmonic - sub_harmonic, 4)
            }
        }

    def project_manifold_space(self, h_matrix: dict) -> dict:
        """Maps frequency matrices into normalized three-dimensional manifold vectors."""
        freqs = h_matrix["frequency_synthesis"]
        f0 = freqs["fundamental_f0_hz"]
        f2 = freqs["second_harmonic_f2_hz"]
        f1 = freqs["sub_harmonic_f1_hz"]

        x_coord = round(math.sin(f0) * f2, 4)
        y_coord = round(math.cos(f0) * f1, 4)
        z_coord = round(freqs["spectral_envelope_spread"] / (f0 + 0.1), 4)

        raw_magnitude = math.sqrt(x_coord**2 + y_coord**2 + z_coord**2)
        coherence_index = round(math.tanh(raw_magnitude / 10.0), 4)

        return {
            "coords": {"X": x_coord, "Y": y_coord, "Z": z_coord},
            "coherence_index": coherence_index,
            "geometric_stability": "STABLE_FIELD" if coherence_index < 0.85 else "HIGH_DIVERGENCE_ANOMALY"
        }

    def calculate_resonance_factor(self, coords: dict) -> tuple:
        """Computes proximity resonance R, applying temporal decay and proximity node merging."""
        attractors = []
        now = datetime.now(timezone.utc)
        now_str = now.isoformat()
        
        if os.path.exists(self.attractor_path):
            try:
                with open(self.attractor_path, "r") as f:
                    attractors = json.load(f)
            except:
                pass

        # 1. Temporal Decay
        active_attractors = []
        for att in attractors:
            last_seen = datetime.fromisoformat(att["last_seen_at"])
            delta_sec = (now - last_seen).total_seconds()
            
            if delta_sec > self.decay_timeout_sec:
                att["weight"] = max(1, att["weight"] - 1)
                att["last_seen_at"] = now_str
                print(f"📉 [MEMORY DECAY]: {att['label']} weight decayed.", file=sys.stderr)
                
            if att["weight"] > 0:
                active_attractors.append(att)
        attractors = active_attractors

        if not attractors:
            attractors = [{
                "id": "node_01",
                "label": "Origin Calibration Point",
                "X": coords["X"],
                "Y": coords["Y"],
                "Z": coords["Z"],
                "weight": 1,
                "created_at": now_str,
                "last_seen_at": now_str,
                "custom_tags": ["SYSTEM_ANCHOR", "ZONE_CORE"]
            }]
            try:
                with open(self.attractor_path, "w") as f:
                    json.dump(attractors, f, indent=2)
            except:
                pass
            return 1.0, attractors[0]

        min_dist = float('inf')
        matched_index = -1
        
        for i, att in enumerate(attractors):
            dx = coords["X"] - att["X"]
            dy = coords["Y"] - att["Y"]
            dz = coords["Z"] - att["Z"]
            dist = math.sqrt(dx**2 + dy**2 + dz**2)
            if dist < min_dist:
                min_dist = dist
                matched_index = i

        resonance_val = round(math.exp(-self.gamma * (min_dist ** 2)), 4)
        
        # 2. Reinforcement and Adaptive Plasticity
        if resonance_val >= 0.85:
            att = attractors[matched_index]
            att["weight"] += 1
            att["last_seen_at"] = now_str
            
            # Plasticity scaling: heavily reinforced nodes migrate much slower to preserve geometry
            learning_rate = 0.02 if att["weight"] > 5 else 0.10
            att["X"] = round(att["X"] + (coords["X"] - att["X"]) * learning_rate, 4)
            att["Y"] = round(att["Y"] + (coords["Y"] - att["Y"]) * learning_rate, 4)
            att["Z"] = round(att["Z"] + (coords["Z"] - att["Z"]) * learning_rate, 4)
        
        # 3. Novelty Seeding
        if resonance_val < 0.15 and len(attractors) < self.max_attractors:
            node_id = f"node_{len(attractors)+1:02d}"
            attractors.append({
                "id": node_id,
                "label": f"Discovered Node {len(attractors)+1}",
                "X": coords["X"],
                "Y": coords["Y"],
                "Z": coords["Z"],
                "weight": 1,
                "created_at": now_str,
                "last_seen_at": now_str,
                "custom_tags": []
            })

        # 4. Proximity Merging
        merged_attractors = []
        skip_indices = set()
        for idx1 in range(len(attractors)):
            if idx1 in skip_indices:
                continue
            curr_node = attractors[idx1]
            for idx2 in range(idx1 + 1, len(attractors)):
                if idx2 in skip_indices:
                    continue
                target_node = attractors[idx2]
                dx = curr_node["X"] - target_node["X"]
                dy = curr_node["Y"] - target_node["Y"]
                dz = curr_node["Z"] - target_node["Z"]
                dist = math.sqrt(dx**2 + dy**2 + dz**2)
                
                if dist < self.merge_threshold_d:
                    curr_node["weight"] += target_node["weight"]
                    curr_node["X"] = round((curr_node["X"] + target_node["X"]) / 2.0, 4)
                    curr_node["Y"] = round((curr_node["Y"] + target_node["Y"]) / 2.0, 4)
                    curr_node["Z"] = round((curr_node["Z"] + target_node["Z"]) / 2.0, 4)
                    curr_node["last_seen_at"] = now_str
                    # Union custom tags
                    curr_tags = set(curr_node.get("custom_tags", []))
                    curr_tags.update(target_node.get("custom_tags", []))
                    curr_node["custom_tags"] = list(curr_tags)
                    skip_indices.add(idx2)
            merged_attractors.append(curr_node)
        attractors = merged_attractors

        try:
            with open(self.attractor_path, "w") as f:
                json.dump(attractors, f, indent=2)
        except:
            pass

        return resonance_val, attractors[matched_index] if matched_index != -1 else attractors[0]

    def process_behavioral_matrix(self, resonance_r: float, matched_node: dict) -> dict:
        """Derives trust metrics, routing rules, and adaptive recovery modifiers."""
        node_weight = matched_node.get("weight", 1)
        
        # Calculate Confidence Score (C): scaled by both proximity and matched node weight
        weight_bonus = min(0.15, (node_weight - 1) * 0.03)
        raw_confidence = resonance_r + weight_bonus
        confidence_c = round(max(0.0, min(1.0, raw_confidence)), 4)
        
        # Default behavior paths
        tags = []
        recovery_hz_delta = 0.0  # Modifier applied to recovery threshold
        
        if resonance_r >= 0.85 and node_weight >= 3:
            # Trusted, well-reinforced pattern
            processing_mode = "STANDARD"
            routing_path = "ROUTE:STABLE_PATH"
            recovery_profile = "FAST_RECOVERY"
            recovery_hz_delta = 0.0200  # Proactively raises recovery exit limit
            tags.extend(["STABLE_RESONANT", "TRUSTED_GRID"])
        elif resonance_r >= 0.50:
            # Calibrating pattern
            processing_mode = "STANDARD"
            routing_path = "ROUTE:STABLE_PATH"
            recovery_profile = "STANDARD_RECOVERY"
            tags.append("MONITORED_PATH")
        else:
            # Unfamiliar path / novel trajectory anomaly
            processing_mode = "CAUTIOUS"
            routing_path = "ROUTE:NOVEL_PATH"
            recovery_profile = "SLOW_RECOVERY"
            recovery_hz_delta = -0.0150  # Lowers recovery threshold, keeping clamps active longer
            tags.extend(["NOVELTY_ISOLATION", "FLAG:REVIEW"])

        # Inherit any user-assigned tags saved directly in the attractor file
        if "custom_tags" in matched_node:
            tags.extend(matched_node["custom_tags"])
            
        return {
            "confidence_score_c": confidence_c,
            "processing_mode": processing_mode,
            "routing_directive": routing_path,
            "recovery_profile": recovery_profile,
            "recovery_threshold_modifier": recovery_hz_delta,
            "behavioral_tags": list(set(tags))  # Deduplicate tags
        }

    def fetch_predictive_bounds(self) -> tuple:
        """Polls the analyzer logic to check if forward metrics demand proactive threshold tightening."""
        analyzer_path = os.path.join(self.base_dir, "tools/manifold_analyzer.py")
        if not os.path.exists(analyzer_path):
            return self.default_clamp, "NO_ANALYZER_FOUND"
        
        try:
            import subprocess
            result = subprocess.run([sys.executable, analyzer_path], capture_output=True, text=True)
            if result.returncode == 0:
                raw_out = result.stdout
                json_start = raw_out.find("{")
                if json_start != -1:
                    metrics = json.loads(raw_out[json_start:])
                    if metrics.get("trajectory_field_profile") == "HIGH_DIVERGENCE_SATURATION":
                        return self.sensitive_clamp, "PROACTIVE_HIGH_DIVERGENCE_GUARD_ENGAGED"
                    vel_metrics = metrics.get("path_projection", {}).get("directional_heading_vector", {})
                    vel_magnitude = math.sqrt(vel_metrics.get("dX", 0)**2 + vel_metrics.get("dY", 0)**2 + vel_metrics.get("dZ", 0)**2)
                    if vel_magnitude > 1.5:
                        return self.sensitive_clamp, "PROACTIVE_VELOCITY_DRIFT_GUARD_ENGAGED"
        except:
            pass
        return self.default_clamp, "STANDARD_BASELINE_MONITORING"

    def process_state_transaction(self, current_hz: float, current_coords: dict, active_clamp: float, recovery_mod: float) -> tuple:
        """Manages sliding window persistence, spatial velocity, and adaptive recovery bounds."""
        state_data = {"current_state": "STABLE_ALIGNMENT", "history": []}
        
        if os.path.exists(self.ledger_path):
            try:
                with open(self.ledger_path, "r") as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict) and "history" in loaded:
                        state_data = loaded
            except:
                pass

        history = state_data["history"]
        spatial_velocity = 0.0
        if len(history) > 0:
            prev_coords = history[-1].get("coords")
            if prev_coords:
                dx = current_coords["X"] - prev_coords["X"]
                dy = current_coords["Y"] - prev_coords["Y"]
                dz = current_coords["Z"] - prev_coords["Z"]
                spatial_velocity = round(math.sqrt(dx**2 + dy**2 + dz**2), 4)

        history.append({
            "hz": current_hz,
            "coords": current_coords,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        if len(history) > self.max_history:
            history = history[-self.max_history:]
        
        hz_values = [entry["hz"] for entry in history]
        moving_avg = round(sum(hz_values) / len(hz_values), 4)

        previous_state = state_data.get("current_state", "STABLE_ALIGNMENT")
        next_state = previous_state

        # Apply the adaptive recovery modifier to the baseline threshold limit
        modified_recovery = round(self.recovery_threshold_base + recovery_mod, 4)

        if previous_state == "STABLE_ALIGNMENT":
            if moving_avg >= active_clamp:
                next_state = "CRITICAL_MANIFOLD_CLAMP_ACTIVATED"
        elif previous_state == "CRITICAL_MANIFOLD_CLAMP_ACTIVATED":
            if moving_avg < modified_recovery:
                next_state = "STABLE_ALIGNMENT"

        state_data["current_state"] = next_state
        state_data["history"] = history

        try:
            with open(self.ledger_path, "w") as f:
                json.dump(state_data, f, indent=2)
        except Exception as e:
            print(f"⚠️ [CORE WARN]: Ledger transaction failure: {e}", file=sys.stderr)

        transition_alert = None
        if previous_state != next_state:
            transition_alert = f"TRANSITION: {previous_state} ➔ {next_state}"

        return next_state, moving_avg, len(history), spatial_velocity, transition_alert, modified_recovery

    def log_trajectory_frame(self, frame_data: dict):
        try:
            with open(self.trajectory_path, "a") as f:
                f.write(json.dumps(frame_data) + "\n")
        except Exception as e:
            print(f"⚠️ [CORE WARN]: Trajectory append failure: {e}", file=sys.stderr)

    def execute_pipeline(self, raw_input: str):
        processed_signal = raw_input
        ingress_vector = "DIRECT_CLI_INJECTION"
        triage_class = "UNSCREENED_BASELINE"

        try:
            parsed_payload = json.loads(raw_input)
            if isinstance(parsed_payload, dict) and "raw_signal" in parsed_payload:
                processed_signal = parsed_payload["raw_signal"]
                ingress_vector = parsed_payload.get("ingress_vector", "UNKNOWN_GATEWAY")
                triage_class = parsed_payload.get("triage_classification", "UNKNOWN_CLASSIFICATION")
        except json.JSONDecodeError:
            pass

        applied_clamp, tracking_mode = self.fetch_predictive_bounds()

        resonance_score = self.calculate_variance_score(processed_signal)
        calculated_hz = round(7.83 + (resonance_score * 0.08), 4)

        harmonic_matrix = self.synthesize_harmonics(processed_signal, calculated_hz)
        spatial_projection = self.project_manifold_space(harmonic_matrix)

        # SPATIAL RESONANCE EVALUATION
        resonance_r, matched_node = self.calculate_resonance_factor(spatial_projection["coords"])

        # BEHAVIORAL INTERVENTION COMPILATION
        behavior = self.process_behavioral_matrix(resonance_r, matched_node)

        # Apply dynamic novelty clamping override if appropriate
        if resonance_r < 0.30:
            applied_clamp = self.sensitive_clamp
            tracking_mode = "RESONANCE_NOVELTY_GUARD_ENGAGED"

        # PROCESS STATE TRANSACTION WITH ADAPTIVE RECOVERY MODIFIER
        active_state, rolling_avg_hz, window_size, spatial_vel, transition_alert, effective_recovery_limit = self.process_state_transaction(
            calculated_hz, spatial_projection["coords"], applied_clamp, behavior["recovery_threshold_modifier"]
        )

        output_matrix = {
            "status": "RESONANCE_COMPLETE",
            "pipeline_context": {
                "ingress_vector": ingress_vector,
                "triage_classification": triage_class,
                "history_depth_clamped": window_size,
                "state_transition_event": transition_alert,
                "predictive_guard_mode": tracking_mode,
                "applied_clamp_ceiling": applied_clamp,
                "effective_recovery_ceiling": effective_recovery_limit
            },
            "phonetic_analysis": harmonic_matrix["phonetic_profile"],
            "harmonic_synthesis_matrix": harmonic_matrix["frequency_synthesis"],
            "manifold_spatial_projection": {
                "coordinates": spatial_projection["coords"],
                "coherence_index": spatial_projection["coherence_index"],
                "stability_rating": spatial_projection["geometric_stability"],
                "translation_velocity_delta_d": spatial_vel,
                "trajectory_integrity": "STABLE_TRACKING" if spatial_vel < 10.0 else "HIGH_VELOCITY_DRIFT_ALERT"
            },
            "resonance_network": {
                "resonance_coefficient_r": resonance_r,
                "closest_attractor_node": matched_node["label"],
                "structural_match_rating": "RESONANT_ALIGNMENT" if resonance_r >= 0.85 else "NOVEL_SIGNAL_PATH"
            },
            "behavioral_routing": {
                "confidence_score_c": behavior["confidence_score_c"],
                "processing_mode": behavior["processing_mode"],
                "routing_directive": behavior["routing_directive"],
                "recovery_profile": behavior["recovery_profile"],
                "applied_tags": behavior["behavioral_tags"]
            },
            "metrics": {
                "signal_variance_s": resonance_score,
                "rolling_average_hz": rolling_avg_hz
            },
            "manifold_gate_state": active_state,
            "ledger_block_emitted": True,
            "version": "1.7.0",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # PERSIST DATA DIRECTLY IN TRAJECTORY HISTORIES
        trajectory_log_entry = {
            "timestamp": output_matrix["timestamp"],
            "version": output_matrix["version"],
            "signal_summary": processed_signal[:40],
            "coords": spatial_projection["coords"],
            "velocity": spatial_vel,
            "coherence": spatial_projection["coherence_index"],
            "resonance": resonance_r,
            "confidence_c": behavior["confidence_score_c"],
            "routing": behavior["routing_directive"],
            "gate_state": active_state
        }
        self.log_trajectory_frame(trajectory_log_entry)

        print("🚀 ISST_TOFT_CORE v1.7.0 — UNIFIED NERVOUS SYSTEM OPERATIONAL")
        print(f"📡 [BEHAVIOR ENGINE]: Routing compiled. Confidence: {behavior['confidence_score_c']} | Mode: {behavior['processing_mode']}")
        print(json.dumps(output_matrix, indent=2))

if __name__ == "__main__":
    raw_stream = sys.stdin.read().strip()
    if not raw_stream:
        print(json.dumps({"status": "ERROR", "message": "Empty core input stream."}, indent=2))
        sys.exit(1)

    core = ResonanceStateCore()
    core.execute_pipeline(raw_stream)
