#!/usr/bin/env python3
import os
import hashlib
from typing import Tuple, Optional

class HandshakeProtocol:
    def __init__(self, shared_secret: bytes = None):
        self.shared_secret = shared_secret or os.urandom(32)
        self.session_key: Optional[bytes] = None
        self.nonce: Optional[bytes] = None
        self.client_nonce: Optional[bytes] = None

    def client_hello(self) -> bytes:
        """Client initiates the handshake."""
        self.nonce = os.urandom(16)
        hello = b"HELLO:" + self.nonce
        return hello

    def server_hello(self, client_hello: bytes) -> bytes:
        """Server responds with challenge."""
        if not client_hello.startswith(b"HELLO:"):
            raise ValueError("Invalid client hello")

        self.client_nonce = client_hello[6:]
        self.nonce = os.urandom(16)

        # Combine nonces + shared secret for challenge
        challenge_data = self.client_nonce + self.nonce + self.shared_secret
        challenge = hashlib.sha256(challenge_data).digest()

        return b"SERVER_HELLO:" + self.nonce + b":" + challenge

    def client_response(self, server_hello: bytes) -> bytes:
        """Client computes and sends response."""
        if not server_hello.startswith(b"SERVER_HELLO:"):
            raise ValueError("Invalid server hello")

        parts = server_hello.split(b":", 2)
        if len(parts) != 3:
            raise ValueError("Malformed server hello")

        server_nonce = parts[1]
        received_challenge = parts[2]

        # Verify server's challenge
        expected_challenge = hashlib.sha256(
            self.nonce + server_nonce + self.shared_secret
        ).digest()

        if received_challenge != expected_challenge:
            raise ValueError("Server challenge verification failed")

        # Generate session key
        key_material = self.nonce + server_nonce + self.shared_secret
        self.session_key = hashlib.pbkdf2_hmac(
            'sha256', key_material, b'salt', 100000, dklen=32
        )

        # Client response (proof of key derivation)
        response = hashlib.sha256(self.session_key + b"CLIENT_OK").digest()
        return b"CLIENT_RESPONSE:" + response

    def server_final(self, client_response: bytes) -> bool:
        """Server verifies client's response and finalizes."""
        if not client_response.startswith(b"CLIENT_RESPONSE:"):
            raise ValueError("Invalid client response")

        received_proof = client_response.split(b":", 1)[1]

        # Fixed: Server derives its own copy of the session key before running the proof check
        if self.session_key is None:
            if self.client_nonce is None or self.nonce is None:
                raise ValueError("Server state missing required nonces to finalize key.")
            key_material = self.client_nonce + self.nonce + self.shared_secret
            self.session_key = hashlib.pbkdf2_hmac(
                'sha256', key_material, b'salt', 100000, dklen=32
            )

        # Recompute expected proof using the derived key
        expected_proof = hashlib.sha256(self.session_key + b"CLIENT_OK").digest()

        if received_proof != expected_proof:
            return False

        return True

    def get_session_key(self) -> Optional[bytes]:
        return self.session_key

if __name__ == "__main__":
    shared_secret = b"super_secret_key_123"
    client = HandshakeProtocol(shared_secret)
    server = HandshakeProtocol(shared_secret)

    hello = client.client_hello()
    print(f"Client Hello:    {hello.hex()[:30]}...")
    
    server_hello = server.server_hello(hello)
    print(f"Server Hello:    {server_hello.hex()[:30]}...")
    
    client_resp = client.client_response(server_hello)
    print(f"Client Response: {client_resp.hex()[:30]}...")
    
    success = server.server_final(client_resp)
    print(f"Handshake successful: {success}")
    if success:
        print(f"Client Key Matrix:   {client.get_session_key().hex()[:24]}...")
        print(f"Server Key Matrix:   {server.get_session_key().hex()[:24]}...")
