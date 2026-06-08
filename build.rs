fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("cargo:rerun-if-changed=proto/combined_manifold.proto");
    println!("cargo:rerun-if-changed=proto/manifold.proto");

    // Explicitly compile both targets inside the same compilation pass
    tonic_build::configure()
        .build_server(true)
        .build_client(true)
        .compile(
            &["proto/combined_manifold.proto", "proto/manifold.proto"],
            &["proto"],
        )?;
    Ok(())
}
