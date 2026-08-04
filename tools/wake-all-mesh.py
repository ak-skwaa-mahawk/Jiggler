import os
import sys
import subprocess

print("================================================================================")
print("🌌  MASTER ORCHESTRATOR — INTEGRATING BOOT INITIALIZATION TO SOVEREIGN RUNTIME")
print("================================================================================")

# Execute the rehydration engine directly as the final step of the boot phase
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import and trigger the active rehydration routine directly inside the process memory space
try:
    print("🚀 Boot validation sequence clearing boundaries. Handing over to runtime...")
    import tools.rehydrate_and_force
except ImportError:
    # Fallback to direct script invocation if paths vary across local configurations
    subprocess.run([sys.executable, "tools/rehydrate_and_force.py"])
