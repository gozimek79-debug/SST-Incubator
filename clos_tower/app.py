"""CLOS Control Tower – FastAPI entrypoint."""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from clos_tower.api.experiments import router as experiments_router
from clos_tower.api.registry import router as registry_router
from clos_tower.streaming.tick_stream import tick_streamer
from clos_tower.integration.cli_bridge import run_demo_stream
import asyncio
import threading

app = FastAPI(title="CLOS Control Tower v0.2")

app.include_router(experiments_router, prefix="/api/experiments", tags=["experiments"])
app.include_router(registry_router, prefix="/api/registry", tags=["registry"])


@app.get("/")
async def root():
    return {"service": "CLOS Control Tower", "version": "0.2", "status": "running"}


@app.websocket("/stream/{run_id}")
async def stream_tick(websocket: WebSocket, run_id: str):
    """WebSocket endpoint – streamuje ticki w czasie rzeczywistym."""
    await websocket.accept()
    await tick_streamer.subscribe(websocket)

    try:
        while True:
            # Czekaj na wiadomości klienta (keepalive)
            await websocket.receive_text()
    except WebSocketDisconnect:
        await tick_streamer.unsubscribe(websocket)


@app.post("/run/demo/stream")
async def start_demo_stream(seed: int = 42, ticks: int = 200):
    """Uruchom demo w tle i streamuj ticki."""
    def run_and_stream():
        generator = run_demo_stream(seed=seed, ticks=ticks)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(tick_streamer.stream_from_generator(generator))

    thread = threading.Thread(target=run_and_stream, daemon=True)
    thread.start()

    return {
        "status": "started",
        "run_id": "demo_shock",
        "seed": seed,
        "ticks": ticks,
        "stream_endpoint": f"/stream/demo_shock"
    }
