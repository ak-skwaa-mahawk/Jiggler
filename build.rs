cat << 'EOF' > build.rs
fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Compiles the new combined proto schema layout into the target OUT_DIR path
    tonic_compile_io::compile_proto("proto/combined_manifold.proto")?;
    Ok(())
}
EOF


fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Compile the proto schema into the target directory out-path
    tonic_build::compile_protos("proto/issttoft.proto")?;
    Ok(())
}
