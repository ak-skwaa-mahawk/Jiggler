# Initialization inside deployment harness
filter_pipeline = ThreadSafeMovingAverageFilter(window_size=4, dimensions=3)
pid_stabilizer = TGSController(Kp=2.5, Ki=0.8, Kd=0.2)

# Inside the running thread execution loop:
while manifold_env.is_running:
    # 1. Sense: Read noisy telemetry
    telemetry = manifold_env.get_telemetry()
    raw_drift = telemetry["v_drift"]
    
    # 2. Filter: Clean sensor artifacts
    clean_drift = filter_pipeline.process_sample(raw_drift)
    
    # 3. Analyze & Act: Pass clean data to control formulas
    # The derivative component now acts on stable trends instead of random noise spikes.
    correction = pid_stabilizer.calculate_correction(clean_drift, telemetry["kappa"], dt=0.02)
    
    # Expose output to deployment shared registers
    shared_registers["correction"] = correction
