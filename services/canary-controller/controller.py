import os, time, json, requests, yaml

PROM = os.getenv("PROMETHEUS_URL", "http://prometheus:9090")
TRAEFIK_PATH = os.getenv("TRAEFIK_DYNAMIC_PATH", "/dynamic/traefik-dynamic.yml")
with open("/SLO.json","r") as f: SLO = json.load(f)

STEPS = [5, 30, 100]
WINDOW_SEC = 60
query_5xx = "(job:http_5xx_rate) or vector(0)"
query_p95 = "(job:http_request_duration_seconds:p95) or vector(0)"

def wait_for_prom(timeout=90, interval=2):
    url = f"{PROM}/-/ready"
    t0 = time.time()
    while time.time()-t0 < timeout:
        try:
            r = requests.get(url, timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(interval)
    print(f"Prometheus not ready after {timeout}s at {url}")
    return False

def q(expr):
    try:
        r = requests.get(f"{PROM}/api/v1/query", params={"query": expr}, timeout=5)
        r.raise_for_status()
        data = r.json()
        if not data["data"]["result"]:
            return 0.0
        return float(data["data"]["result"][0]["value"][1])
    except Exception as e:
        print(f"Query failed for {expr}: {e}")
        return 0.0

def set_weights(v1, v2):
    with open(TRAEFIK_PATH,"r") as f:
        d = yaml.safe_load(f)
    d['http']['services']['canary']['weighted']['services'][0]['weight'] = int(v1)
    d['http']['services']['canary']['weighted']['services'][1]['weight'] = int(v2)
    with open(TRAEFIK_PATH,"w") as f:
        yaml.safe_dump(d, f, sort_keys=False)
    print(f"weights -> v1:{v1} v2:{v2}")

def healthy():
    five_xx = q(query_5xx)
    p95 = q(query_p95)
    ok = five_xx <= SLO['error_rate_5xx']['target'] and p95 <= (SLO['latency_p95_ms']['target']/1000.0)
    print({'5xx': five_xx, 'p95': p95, 'healthy': ok})
    return ok

def run_canary():
    for step in STEPS:
        set_weights(100-step, step)
        print(f"canary {step}% for {WINDOW_SEC}s...")
        t0 = time.time()
        while time.time()-t0 < WINDOW_SEC:
            if not healthy():
                print("BREACH → rollback")
                set_weights(100, 0)
                return False
            time.sleep(5)
    print("Promote 100%")
    set_weights(0, 100)
    return True

if __name__ == "__main__":
    wait_for_prom()
    ok = run_canary()
    with open("/app/result.txt","w") as f:
        f.write("promoted" if ok else "rolled back")
