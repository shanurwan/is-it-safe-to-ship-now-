import os, random, time
from fastapi import FastAPI, Request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

app = FastAPI()

REQUESTS = Counter('http_requests_total', 'Total requests', ['status'])
LATENCY = Histogram('http_request_duration_seconds','Request latency seconds',buckets=(0.025,0.05,0.1,0.25,0.5,1,2))

DEFECT_RATE = float(os.getenv("DEFECT_RATE", "0"))
SLOW_MODE = int(os.getenv("SLOW_MODE", "0"))

@app.middleware("http")
async def metrics_mw(request: Request, call_next):
    start = time.time()
    try:
        if SLOW_MODE:
            time.sleep(0.3)
        if random.random() < DEFECT_RATE:
            REQUESTS.labels(status="500").inc()
            LATENCY.observe(time.time()-start)
            return Response(status_code=500)
        resp = await call_next(request)
        status = resp.status_code
    except Exception:
        status = 500
        raise
    finally:
        LATENCY.observe(time.time()-start)
        REQUESTS.labels(status=str(status)).inc()
    return resp

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
