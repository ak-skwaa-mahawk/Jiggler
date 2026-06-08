cat << 'EOF' > run_manifold.py
import argparse
import subprocess
import sys
import time

def main():
    parser = argparse.ArgumentParser(description="Tordial Manifold Optimization Execution Harness")
    parser.add_argument("--nodes", type=int, default=10)
    parser.add_argument("--cycles", type=int, default=180)
    parser.add_argument("--engine", type=str, default="native")
    args = parser.parse_args()

    print(f"[🌀] Initializing Tordial Manifold Array: {args.nodes} Nodes | {args.cycles} Cycles")
    
    if args.engine == "native":
        print("[🚀] Launching high-performance native Rust substrate...")
        try:
            # Deploy your compiled release binary as a persistent background server process
            proc = subprocess.Popen(["./target/release/tordial_gs_manifold"])
            print(f"[🔥] Substrate successfully locked down on PID {proc.pid}. Running background process.")
            time.sleep(1.5)  # Let socket finish binding to port 50051
        except Exception as e:
            print(f"❌ Failed to execute native substrate binary: {e}")
            sys.exit(1)
    else:
        print(f"[⚠️] Unknown engine runtime mode: {args.engine}")

if __name__ == "__main__":
    main()
EOF
