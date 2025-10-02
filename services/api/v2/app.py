import os
import random
import time
import asyncio
from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

app = FastAPI()

REQUESTS = Counter("http_requests_total", "Total requests", ["status"])
LATENCY = Histogram(
    "http_request_duration_seconds",
    "Request latency seconds",
    buckets=(0.025, 0.05, 0.1, 0.25, 0.5, 1, 2),
)

DEFECT_RATE = float(os.getenv("DEFECT_RATE", "0"))
SLOW_MODE = int(os.getenv("SLOW_MODE", "0"))


@app.middleware("http")
async def metrics_mw(request: Request, call_next):
    start = time.perf_counter()
    status = 500  # default if an exception occurs

    try:
        if SLOW_MODE:
            # don't block the event loop
            await asyncio.sleep(0.3)

        # probabilistic defect response
        if random.random() < DEFECT_RATE:
            status = 500
            return Response(status_code=status)

        resp = await call_next(request)
        status = resp.status_code
        return resp
    except Exception:
        # re-raise after recording metrics in finally
        raise
    finally:
        LATENCY.observe(time.perf_counter() - start)
        REQUESTS.labels(status=str(status)).inc()


@app.get("/")
def root():
    return {"version": os.getenv("VERSION", "v2"), "ok": True}


@app.get("/toggle")
def toggle(defect: float | None = None, slow: int | None = None):
    global DEFECT_RATE, SLOW_MODE
    if defect is not None:
        DEFECT_RATE = float(defect)
    if slow is not None:
        SLOW_MODE = int(slow)
    return {"DEFECT_RATE": DEFECT_RATE, "SLOW_MODE": SLOW_MODE}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
