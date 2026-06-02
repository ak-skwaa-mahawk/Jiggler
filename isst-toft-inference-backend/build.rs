// build.rs
// ISST-TOFT Sovereign Inference Backend — Build Script
//
// Generates both server (InferenceServiceServer) and client (InferenceServiceClient)
// stubs from the sovereign .proto definition using tonic + prost.
//
// This configuration is optimized for:
// - Clean workspace builds
// - Deterministic incremental compilation
// - Maximum auditability (no hidden codegen side effects)

use std::path::PathBuf;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Re-run this script only when the proto definition changes.
    // Critical for sovereign reproducibility and CI caching.
    println!("cargo:rerun-if-changed=proto/isst_toft.proto");

    let proto_dir = PathBuf::from("proto");

    tonic_build::configure()
        // Explicitly request both server and client code generation
        .build_server(true)
        .build_client(true)
        // Keep generated code in OUT_DIR (default). This keeps the src/ tree clean
        // and avoids committing generated files to the repository.
        //
        // If you ever need the generated files visible for inspection, you can
        // temporarily change this to a fixed path like "src/generated".
        .compile(&[proto_dir.join("isst_toft.proto")], &[proto_dir])?;

    // Optional: emit a warning so the build log clearly shows the sovereign gRPC layer was built
    println!("cargo:warning=ISST-TOFT gRPC codegen complete (server + client stubs ready)");

    Ok(())
}