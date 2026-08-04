cat << 'EOF' > build.rs
fn main() -> Result<(), Box<dyn std::error::Error>> {
    # Pass the proto path directly as a standard &str reference
    tonic_build::compile_protos("proto/combined_manifold.proto")?;
    Ok(())
}
EOF


cat << 'EOF' > build.rs
fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Coerce the arrays into slice views matching &[impl AsRef<Path>]
    let protos = &["proto/combined_manifold.proto"];
    let includes = &["proto"];
    
    tonic_build::compile_protos(protos, includes)?;
    Ok(())
}
EOF

cat << 'EOF' > build.rs
fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Pass the unified schema path as a borrowed array slice to satisfy compile_protos
    tonic_build::compile_protos(&["proto/combined_manifold.proto"])?;
    Ok(())
}
EOF

cat << 'EOF' > build.rs
fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Uses the native tonic_build compiler engine to generate the combined stubs
    tonic_build::compile_proto("proto/combined_manifold.proto")?;
    Ok(())
}
EOF

