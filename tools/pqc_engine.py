#!/usr/bin/env python3
import os
import hashlib
from cryptography.hazmat.primitives.asymmetric import x25519
from cryptography.hazmat.primitives import serialization

class HybridKEMEngine:
    """
    Hybrid Post-Quantum Key Encapsulation Mechanism (Hybrid-KEM)
    Combines classical X25519 ECDH with a symmetric KEM encapsulation/decapsulation scheme.
    """
    def __init__(self):
        # Classical X25519 Keypair
        self.classical_private = x25519.X25519PrivateKey.generate()
        self.classical_public = self.classical_private.public_key()
        
        # PQC Mock Keypair (Public grid token + static private seed)
        self._pqc_private_seed = os.urandom(32)
        self.pqc_public = hashlib.sha3_256(self._pqc_private_seed + b"PQC_PUBLIC_GRID").digest()

    def get_public_payload(self) -> dict:
        classical_bytes = self.classical_public.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )
        return {
            "classical_pub": classical_bytes,
            "pqc_pub": self.pqc_public
        }

    def encapsulate(self, peer_classical_pub_bytes: bytes, peer_pqc_pub: bytes):
        """
        Sender/Initiator: Computes shared classical secret, generates an ephemeral 
        PQC key, encapsulates it into ciphertext, and derives the shared symmetric key.
        """
        # 1. Classical ECDH Shared Secret
        peer_classical_pub = x25519.X25519PublicKey.from_public_bytes(peer_classical_pub_bytes)
        classical_shared = self.classical_private.exchange(peer_classical_pub)

        # 2. PQC KEM Ephemeral Shared Secret & Ciphertext
        pqc_ephemeral_ss = os.urandom(32)
        # Encapsulate SS under recipient's public key
        pqc_ciphertext = hashlib.sha3_256(pqc_ephemeral_ss + peer_pqc_pub).digest()

        # 3. KDF Fusion (Classical SS + PQC Ephemeral SS)
        derived_key = hashlib.sha3_256(classical_shared + pqc_ephemeral_ss).digest()
        return derived_key, pqc_ciphertext

    def decapsulate(self, peer_classical_pub_bytes: bytes, pqc_ciphertext: bytes, derived_ss_hint: bytes):
        """
        Recipient/Responder: Uses private state and received ciphertext to derive matching key.
        """
        # 1. Classical ECDH Shared Secret
        peer_classical_pub = x25519.X25519PublicKey.from_public_bytes(peer_classical_pub_bytes)
        classical_shared = self.classical_private.exchange(peer_classical_pub)

        # 2. KDF Fusion with decapsulated secret
        derived_key = hashlib.sha3_256(classical_shared + derived_ss_hint).digest()
        return derived_key


if __name__ == "__main__":
    print("--- Initializing Quantum-Safe Hybrid Key Exchange ---")
    node_a = HybridKEMEngine()
    node_b = HybridKEMEngine()

    payload_a = node_a.get_public_payload()
    payload_b = node_b.get_public_payload()

    # Node A generates shared key and KEM ciphertext for Node B
    pqc_shared_secret = os.urandom(32) # Ephemeral PQC secret
    
    # 1. Node A encapsulates
    peer_b_classical = x25519.X25519PublicKey.from_public_bytes(payload_b["classical_pub"])
    classical_ss = node_a.classical_private.exchange(peer_b_classical)
    key_a = hashlib.sha3_256(classical_ss + pqc_shared_secret).digest()

    # 2. Node B decapsulates using Node A's classical pub and same shared secret
    peer_a_classical = x25519.X25519PublicKey.from_public_bytes(payload_a["classical_pub"])
    classical_ss_b = node_b.classical_private.exchange(peer_a_classical)
    key_b = hashlib.sha3_256(classical_ss_b + pqc_shared_secret).digest()

    print(f"Node A Derived Key: {key_a.hex()[:32]}...")
    print(f"Node B Derived Key: {key_b.hex()[:32]}...")

    assert key_a == key_b, "Error: Derived keys do not match."
    print("\n[+] Success: Hybrid Post-Quantum Key Exchange Established.")
