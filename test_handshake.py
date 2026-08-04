import hashlib
import os
from typing import Optional

class HandshakeProtocol:
    def __init__(self, shared_secret: bytes = None):
        self.shared_secret = shared_secret or os.urandom(32)
        self.session_key: Optional[bytes] = None
        self.nonce: Optional[bytes] = None
        self.peer_nonce: Optional[bytes] = None  # Tracks the other side's nonce

    def client_hello(self) -> bytes:
        """Client initiates the handshake by creating a local nonce."""
        self.nonce = os.urandom(16)
        return b"HELLO:" + self.nonce

    def server_hello(self, client_hello: bytes) -> bytes:
        """Server parses client nonce and responds with its own nonce and a challenge."""
        if not client_hello.startswith(b"HELLO:"):
            raise ValueError("Invalid client hello")
        
        self.peer_nonce = client_hello[6:]  # Store client's nonce
        self.nonce = os.urandom(16)        # Generate server's nonce
        
        # Challenge verifies that the server knows the shared secret
        challenge_data = self.peer_nonce + self.nonce + self.shared_secret
        challenge = hashlib.sha256(challenge_data).digest()
        
        return b"SERVER_HELLO:" + self.nonce + b":" + challenge

    def client_response(self, server_hello: bytes) -> bytes:
        """Client verifies server's challenge and derives the session key."""
        if not server_hello.startswith(b"SERVER_HELLO:"):
            raise ValueError("Invalid server hello")
        
        parts = server_hello.split(b":", 2)
        if len(parts) != 3:
            raise ValueError("Malformed server hello")
        
        server_nonce = parts[1]
        received_challenge = parts[2]
        
        # Verify the server's identity using the client's original nonce
        expected_challenge = hashlib.sha256(
            self.nonce + server_nonce + self.shared_secret
        ).digest()
        
        if received_challenge != expected_challenge:
            raise ValueError("Server challenge verification failed")
        
        # Client derives the symmetric session key
        key_material = self.nonce + server_nonce + self.shared_secret
        self.session_key = hashlib.pbkdf2_hmac(
            'sha256', key_material, b'salt', 100000, dklen=32
        )
        
        # Create proof of key derivation to send back to the server
        response = hashlib.sha256(self.session_key + b"CLIENT_OK").digest()
        return b"CLIENT_RESPONSE:" + response

    def server_final(self, client_response: bytes) -> bool:
        """Server derives its own copy of the key and verifies client's proof."""
        if not client_response.startswith(b"CLIENT_RESPONSE:"):
            raise ValueError("Invalid client response")
        
        received_proof = client_response.split(b":", 1)[1]
        
        # Server derives the symmetric session key using stored components
        key_material = self.peer_nonce + self.nonce + self.shared_secret
        self.session_key = hashlib.pbkdf2_hmac(
            'sha256', key_material, b'salt', 100000, dklen=32
        )
        
        expected_proof = hashlib.sha256(self.session_key + b"CLIENT_OK").digest()
        return received_proof == expected_proof

    def get_session_key(self) -> Optional[bytes]:
        return self.session_key

if __name__ == "__main__":
    shared_secret = b"super_secret_key_123"
    
    client = HandshakeProtocol(shared_secret)
    server = HandshakeProtocol(shared_secret)
    
    # Execution Loop
    hello = client.client_hello()
    server_hello = server.server_hello(hello)
    client_resp = client.client_response(server_hello)
    success = server.server_final(client_resp)
    
    print(f"Handshake successful: {success}")
    if success:
        print(f"Session key established: {server.get_session_key().hex()[:32]}...")
