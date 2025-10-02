from fastapi import FastAPI, Request
import yaml
import os

TRAEFIK_PATH = os.getenv("TRAEFIK_DYNAMIC_PATH", "/dynamic/traefik-dynamic.yml")

app = FastAPI()


def set_weights(v1: int, v2: int) -> None:
    """Update Traefik canary weights (v1 + v2 should be 100)."""
    with open(TRAEFIK_PATH, "r") as f:
        data = yaml.safe_load(f)

    # Expecting the structure set earlier in your Traefik dynamic config
    services = data["http"]["services"]["canary"]["weighted"]["services"]
    services[0]["weight"] = int(v1)
    services[1]["weight"] = int(v2)

    with open(TRAEFIK_PATH, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)


@app.post("/alerts")
async def alerts(req: Request):
    payload = await req.json()
    # On any firing alert with severity=page, rollback.
    for a in payload.get("alerts", []):
        if (
            a.get("status") == "firing"
            and a.get("labels", {}).get("severity") == "page"
        ):
            set_weights(100, 0)
            return {"action": "rollback"}
    return {"action": "noop"}
