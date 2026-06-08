import logging
from fastapi import FastAPI
from api.manifold import router as manifold_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="Tordial GS Manifold API Gateway", version="1.0.0-ALGEBRA")
app.include_router(manifold_router)

@app.get("/")
async def root_health_check():
    return {"status": "ONLINE", "substrate_bridge": "READY"}

logger.info("🛰️  FastAPI Core Engine successfully linked to manifold router matrix.")
