import os, time
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


@app.middleware("http")
async def metrics_mw(request: Request, call_next):
    start = time.time()
    try:
        resp = await call_next(request)
        status = resp.status_code
    except Exception:
        status = 500
        raise
    finally:
        LATENCY.observe(time.time() - start)
        REQUESTS.labels(status=str(status)).inc()
    return resp


@app.get("/")
def root():
    return {"version": os.getenv("VERSION", "v1"), "ok": True}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
