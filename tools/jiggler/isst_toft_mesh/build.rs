python -c '
with open("build.rs", "w") as f:
    f.write("""fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("cargo:rerun-if-changed=proto/isst_toft.proto");
    
    tonic_build::configure()
        .build_server(true)
        .build_client(true)
        .compile(
            &["proto/isst_toft.proto"],
            &["proto"]
        )?;
        
    println!("cargo:warning=ISST-TOFT gRPC codegen complete");
    Ok(())
}
""")
print("🚀 Local build.rs successfully modernized.")
'
