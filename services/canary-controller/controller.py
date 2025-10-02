import os
import time
import json
import requests
import yaml

PROM = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
TRAEFIK_PATH = os.getenv("TRAEFIK_DYNAMIC_PATH", "/dynamic/traefik-dynamic.yml")

with open("/SLO.json", "r") as f:
    SLO = json.load(f)

STEPS = [5, 30, 100]  # % traffic to v2 at each step
WINDOW_SEC = 60

query_5xx = "job:http_5xx_rate"
query_p95 = "job:http_request_duration_seconds:p95"


def q(expr: str) -> float:
    """Query a single Prometheus instant vector and return its first value as float, or 0.0."""
    try:
        r = requests.get(f"{PROM}/api/v1/query", params={"query": expr}, timeout=5)
        r.raise_for_status()
        payload = r.json()
        return float(payload["data"]["result"][0]["value"][1])
    except Exception as e:
        print(f"Query failed for {expr}: {e}")
        return 0.0


def set_weights(v1: int, v2: int) -> None:
    """Update Traefik canary weights for v1 and v2 (must sum to 100)."""
    with open(TRAEFIK_PATH, "r") as f:
        data = yaml.safe_load(f)

    # Defensive checks for expected structure
    try:
        services = data["http"]["services"]["canary"]["weighted"]["services"]
        # Assume index 0 is v1 and index 1 is v2 as per your dynamic config
        services[0]["weight"] = int(v1)
        services[1]["weight"] = int(v2)
    except (KeyError, IndexError, TypeError) as e:
        raise RuntimeError(f"Unexpected Traefik config structure: {e}")

    with open(TRAEFIK_PATH, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)

    print(f"weights -> v1:{v1} v2:{v2}")


def healthy() -> bool:
    five_xx = q(query_5xx)
    p95 = q(query_p95)
    ok = five_xx <= SLO["error_rate_5xx"]["target"] and p95 <= (
        SLO["latency_p95_ms"]["target"] / 1000.0
    )
    print({"5xx": five_xx, "p95": p95, "healthy": ok})
    return ok


def run_canary() -> bool:
    for step in STEPS:
        set_weights(100 - step, step)
        print(f"canary {step}% for {WINDOW_SEC}s...")
        t0 = time.time()
        while time.time() - t0 < WINDOW_SEC:
            if not healthy():
                print("BREACH → rollback")
                set_weights(100, 0)
                return False
            time.sleep(5)
    print("Promote 100%")
    set_weights(0, 100)
    return True


if __name__ == "__main__":
    ok = run_canary()
    with open("/app/result.txt", "w") as f:
        f.write("promoted" if ok else "rolled back")
