{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SynaraUserNullroseHandshake",
  "description": "Cryptographic proof-of-presence handshake schema forcing fallback to the Strawman defensive baseline upon signature loss.",
  "type": "object",
  "required": [
    "handshake_id",
    "timestamp_utc",
    "protocol_version",
    "operator_identity",
    "cryptographic_lock",
    "state_vector_digest",
    "fallback_directives"
  ],
  "properties": {
    "handshake_id": {
      "type": "string",
      "format": "uuid"
    },
    "timestamp_utc": {
      "type": "string",
      "format": "date-time"
    },
    "protocol_version": {
      "type": "string",
      "pattern": "^v[0-9]+\\.[0-9]+$"
    },
    "operator_identity": {
      "type": "object",
      "required": ["sovereign_id", "session_token_hash"],
      "properties": {
        "sovereign_id": { "type": "string", "example": "99733-Q" },
        "session_token_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$" }
      }
    },
    "cryptographic_lock": {
      "type": "object",
      "required": ["previous_block_hash", "current_handshake_hash", "signature_algorithm"],
      "properties": {
        "previous_block_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
        "current_handshake_hash": { "type": "string", "pattern": "^[a-f0-9]{64}$" },
        "signature_algorithm": { "type": "string", "enum": ["SHA-256", "Ed25519"] }
      }
    },
    "state_vector_digest": {
      "type": "object",
      "required": ["base_y", "mesh_y", "volume_y", "residual_surplus"],
      "properties": {
        "base_y": { "type": "number", "minimum": 0.0 },
        "mesh_y": { "type": "number", "minimum": 0.0 },
        "volume_y": { "type": "number", "minimum": 0.0 },
        "residual_surplus": { "type": "number" }
      }
    },
    "fallback_directives": {
      "type": "object",
      "required": ["on_handshake_failure", "grace_period_ms", "target_floor_absolute"],
      "properties": {
        "on_handshake_failure": { "type": "string", "enum": ["REVOKE_SOVEREIGNTY", "STRAWMAN_SHIELD_FALLBACK", "FREEZE_MANIFOLD"] },
        "grace_period_ms": { "type": "integer", "default": 0 },
        "target_floor_absolute": { "type": "number", "const": 0.0 }
      }
    }
  }
}