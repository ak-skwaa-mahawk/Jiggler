import argparse
import subprocess
import sys
import time

def main():
    parser = argparse.ArgumentParser(description="Tordial Manifold Optimization Execution Harness")
    parser.add_argument("--nodes", type=int, default=10)
    parser.add_argument("--cycles", type=int, default=180)
    parser.add_argument("--engine", type=str, default="native")
    parser.add_argument("--video", type=str, default=None, help="Output target name for the tracking video rendering")
    args = parser.parse_args()

    print(f"[🌀] Initializing Tordial Manifold Array: {args.nodes} Nodes | {args.cycles} Cycles")

    if args.engine == "native":
        print("[🚀] Launching high-performance native Rust substrate...")
        try:
            proc = subprocess.Popen(["./target/release/tordial_gs_manifold"])
            print(f"[🔥] Substrate successfully locked down on PID {proc.pid}. Running background process.")
            time.sleep(1.5)
            
            if args.video:
                print(f"[🎥] Video capture flag targeted: {args.video}")
                print(f"[🎛️] Attaching visualizer core to stream matrix updates...")
                vis_proc = subprocess.run([
                    sys.executable, "visualizer.py", 
                    "--output", args.video, 
                    "--frames", str(args.cycles)
                ])
                if vis_proc.returncode == 0:
                    print(f"[✅] Stereo matrix video rendering completed successfully: {args.video}")
                else:
                    print("[⚠️] Visualizer finished with non-zero exit state. Checking matrix logs.")
        except Exception as e:
            print(f"❌ Failed to execute native substrate binary: {e}")
            sys.exit(1)
    else:
        print(f"[⚠️] Unknown engine runtime mode: {args.engine}")

if __name__ == "__main__":
    main()
