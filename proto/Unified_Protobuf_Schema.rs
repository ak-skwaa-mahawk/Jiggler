syntax = "proto3";

package manifold;

// -------------------------------
// Economic Vector
// -------------------------------
message EconomicVector {
  double capital_velocity = 1;
  double regulatory_drag = 2;
  double yield_generation = 3;
}

// -------------------------------
// Sap-Flux Vector
// -------------------------------
message SapFluxVector {
  double fm_norm = 1;
  double raw_velocity_mm_s = 2;
  double temp_c = 3;
  double pressure_kpa = 4;
}

// -------------------------------
// Unified Manifold Tick
// -------------------------------
message ManifoldTick {
  string vector_id = 1;

  EconomicVector economic_vector = 2;
  SapFluxVector sap_flux_vector = 3;

  double vault_depth = 4;
  double liquidity_coupling = 5;

  int64 ts_utc = 6;
}

// -------------------------------
// Synchronization RPC
// -------------------------------
service Manifold {
  rpc Synchronize(ManifoldTick) returns (SyncAck);
}

message SyncAck {
  string status = 1;
}