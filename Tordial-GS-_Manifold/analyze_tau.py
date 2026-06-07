cat << 'EOF' > analyze_tau.py
import math

EQUILIBRIUM_MAP = {
    "cERNpiranchor": 0.8742,
    "warpcorestability": 0.6180,
    "sovereignintentprimary": 0.9510,
    "sovereignintentambient": 0.3820,
    "sensorium_feedback": 0.2360,
    "mutationplanedriver": 0.7777
}

LOG_DATA = """
   Stream Packet -> Band: 'mutationplanedriver'    | Value: 0.9990 | Driver: experimental_injection_pulse
   Stream Packet -> Band: 'cERNpiranchor'          | Value: 0.0200 | Driver: coupling_propagation_from_band_5(coeff=0.02)
   Stream Packet -> Band: 'warpcorestability'      | Value: 0.0999 | Driver: coupling_propagation_from_band_5(coeff=0.10)
   Stream Packet -> Band: 'sovereignintentprimary' | Value: 0.0999 | Driver: coupling_propagation_from_band_5(coeff=0.10)
   Stream Packet -> Band: 'sovereignintentambient' | Value: 0.0999 | Driver: coupling_propagation_from_band_5(coeff=0.10)
   Stream Packet -> Band: 'sensorium_feedback'     | Value: 0.0999 | Driver: coupling_propagation_from_band_5(coeff=0.10)
   Stream Packet -> Band: 'warpcorestability'      | Value: 0.1072 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'sensorium_feedback'     | Value: 0.1045 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'cERNpiranchor'          | Value: 0.0217 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'sovereignintentambient' | Value: 0.1089 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'sovereignintentprimary' | Value: 0.1135 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'mutationplanedriver'    | Value: 0.9937 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'warpcorestability'      | Value: 0.1143 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'sensorium_feedback'     | Value: 0.1090 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'cERNpiranchor'          | Value: 0.0234 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'sovereignintentambient' | Value: 0.1177 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'sovereignintentprimary' | Value: 0.1269 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'mutationplanedriver'    | Value: 0.9885 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'warpcorestability'      | Value: 0.1214 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'sensorium_feedback'     | Value: 0.1133 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'cERNpiranchor'          | Value: 0.0251 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'sovereignintentambient' | Value: 0.1261 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'sovereignintentprimary' | Value: 0.1401 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'mutationplanedriver'    | Value: 0.9834 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'warpcorestability'      | Value: 0.1283 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'sensorium_feedback'     | Value: 0.1175 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'cERNpiranchor'          | Value: 0.0268 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'sovereignintentambient' | Value: 0.1343 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'sovereignintentprimary' | Value: 0.1531 | Driver: ambient_field_relaxation
   Stream Packet -> Band: 'mutationplanedriver'    | Value: 0.9785 | Driver: ambient_field_relaxation
"""

def extract_time_series_profiles(raw_logs):
    profiles = {band_id: [] for band_id in EQUILIBRIUM_MAP.keys()}
    for line in raw_logs.strip().split("\n"):
        if "Band:" not in line: continue
        try:
            parts = line.split("|")
            band_id = parts[0].split("Band:")[1].strip().strip("'")
            val_str = parts[1].split("Value:")[1].strip()
            value = float(val_str)
            if band_id in profiles:
                profiles[band_id].append(value)
        except Exception:
            continue
    return profiles

def calculate_characteristic_tau(time_series, x_inf, dt=0.1):
    n = len(time_series)
    if n < 2: return float('inf')
    t_points = [i * dt for i in range(n)]
    y_points = []
    for x in time_series:
        deviation = abs(x - x_inf)
        if deviation <= 0.0: deviation = 1e-6
        y_points.append(math.log(deviation))
    mean_t = sum(t_points) / n
    mean_y = sum(y_points) / n
    num = sum((t_points[i] - mean_t) * (y_points[i] - mean_y) for i in range(n))
    den = sum((t_points[i] - mean_t) ** 2 for i in range(n))
    if den == 0.0: return float('inf')
    slope_b = num / den
    if slope_b >= 0.0: return float('inf')
    return -1.0 / slope_b

if __name__ == "__main__":
    print("══════════════════════════════════════════════════════════════")
    print("🔬  SOVEREIGN MESH TRANSIENT LAB: TAU ANALYSIS")
    print("══════════════════════════════════════════════════════════════")
    series_data = extract_time_series_profiles(LOG_DATA)
    for band, records in series_data.items():
        if not records: continue
        x_inf = EQUILIBRIUM_MAP[band]
        tau = calculate_characteristic_tau(records, x_inf, dt=0.1)
        print(f" 📊 Band: {band:<22} | Samples: {len(records)} | Base Equilibrium: {x_inf:.4f}")
        if tau == float('inf'):
            print(f"    └── 🧮 Estimated Tau (\u03c4): UNDEFINED (Compressive Elastic Recovery)")
        else:
            print(f"    └── 🧮 Estimated Tau (\u03c4): {tau:.4f} seconds")
EOF
