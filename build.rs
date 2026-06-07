fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Compile the proto schema into the target directory out-path
    tonic_build::compile_protos("proto/issttoft.proto")?;
    Ok(())
}
