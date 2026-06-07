cat > topo_extractor/telemetry_parser.py << 'PYEOF'
import re
from .jed_trajectory import JEDTrajectory

def parse_jed_telemetry(log_path: str = "jed_unified_telemetry.log") -> JEDTrajectory:
    """Parses your existing JED telemetry log into a JEDTrajectory object."""
    with open(log_path, "r") as f:
        content = f.read()

    # Extract the cycle table data (robust regex for your format)
    cycle_pattern = r"(\d+)\s+ΔE=([+-]?\d+\.\d+)\s+spin=([\d.]+)\s+temp=([\d.]+)\s+throat=([\d.]+)\s+belt=([\d.]+)\s+task=([\d.]+)\s+coh=([\d.]+)\s+relax=([\d.]+)"
    matches = re.findall(cycle_pattern, content)

    if not matches:
        raise ValueError("Could not parse cycle data from telemetry log")

    cycles = [int(m[0]) for m in matches]
    delta_e = [float(m[1]) for m in matches]
    spin = [float(m[2]) for m in matches]
    temp = [float(m[3]) for m in matches]
    throat = [float(m[4]) for m in matches]
    belt = [float(m[5]) for m in matches]
    task = [float(m[6]) for m in matches]
    coh = [float(m[7]) for m in matches]
    relax = [float(m[8]) for m in matches]

    return JEDTrajectory(
        cycles=cycles,
        delta_e=delta_e,
        spin=spin,
        temp=temp,
        throat=throat,
        belt=belt,
        task=task,
        coh=coh,
        relax=relax
    )
PYEOF