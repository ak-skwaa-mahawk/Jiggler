from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

MANIFOLD_SYNC_URL = "http://127.0.0.1:8000/manifold/synchronize"


class SapFluxPacket(BaseModel):
    id: str
    ts_utc: int
    sap_velocity_mm_s: float
    temp_c: float | None = None
    pressure_kpa: float | None = None


def normalize_fm(packet: SapFluxPacket) -> float:
    # Basic sanity + clamp
    v = max(0.0, min(packet.sap_velocity_mm_s, 200.0))  # domain-specific upper bound
    # Optional: temperature compensation, scaling to [0,1]
    v_norm = v / 200.0
    return v_norm


@router.post("/ingest/sap_flux")
async def ingest_sap_flux(packet: SapFluxPacket):
    try:
        fm_norm = normalize_fm(packet)

        manifold_tick = {
            "vector_id": f"SAP-{packet.id}-{packet.ts_utc}",
            "sap_flux_vector": {
                "fm_norm": fm_norm,
                "raw_velocity_mm_s": packet.sap_velocity_mm_s,
                "temp_c": packet.temp_c,
                "pressure_kpa": packet.pressure_kpa,
            },
            # You can later make these dynamic (e.g., from L_c or region metadata)
            "vault_depth": 21.8566,
            "liquidity_coupling": 1.48,
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(MANIFOLD_SYNC_URL, json=manifold_tick)

        if resp.status_code != 200:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"Manifold sync failed: {resp.text}",
            )

        return {"status": "ok", "fm_norm": fm_norm}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))