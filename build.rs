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



fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Compile the proto schema into the target directory out-path
    tonic_build::compile_protos("proto/issttoft.proto")?;
    Ok(())
}
