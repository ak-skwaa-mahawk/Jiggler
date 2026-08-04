# ====================== TRINITY VIZ ENDPOINT ======================
from core.trinity_harmonics import describe_trinity_state, plot_trinity_harmonics
import base64
from io import BytesIO

@app.get("/trinity-viz")
async def trinity_viz(preset: str = "Balanced", custom_damp: float = None):
    """Live Trinity Dynamics visualization as base64 PNG + JSON data"""
    describe_trinity_state()  # console log for server

    # Generate plot in memory
    fig, ax = plt.subplots(figsize=(11, 7))
    # ... (reuse your existing plot_trinity_harmonics logic here or call it)
    # For simplicity we reuse the function and capture output
    buf = BytesIO()
    plt.savefig(buf, format="png", facecolor="#0a0a0a")
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode("utf-8")

    # Return JSON + image for React
    return {
        "status": "IGNITED",
        "preset": preset,
        "custom_damp": custom_damp,
        "trinity_data": {
            "ground_state": GROUND_STATE,
            "difference": DIFFERENCE,
            "ratio": RATIO,
            "phase": trinity.phase,
            "stability": trinity.trinity_factor(1.0)
        },
        "image": f"data:image/png;base64,{img_base64}"
    }