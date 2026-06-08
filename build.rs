cat << 'EOF' > build.rs
fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Coerce the arrays into slice views matching &[impl AsRef<Path>]
    let protos = &["proto/combined_manifold.proto"];
    let includes = &["proto"];
    
    tonic_build::compile_protos(protos, includes)?;
    Ok(())
}
EOF
