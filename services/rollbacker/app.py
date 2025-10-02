from fastapi import FastAPI, Request
import yaml, os

TRAEFIK_PATH = os.getenv('TRAEFIK_DYNAMIC_PATH', '/dynamic/traefik-dynamic.yml')
app = FastAPI()

def set_weights(v1, v2):
    d = yaml.safe_load(open(TRAEFIK_PATH))
    d['http']['services']['canary']['weighted']['services'][0]['weight'] = int(v1)
    d['http']['services']['canary']['weighted']['services'][1]['weight'] = int(v2)
    open(TRAEFIK_PATH,'w').write(yaml.safe_dump(d))

@app.post('/alerts')
async def alerts(req: Request):
    payload = await req.json()
    for a in payload.get('alerts', []):
        if a.get('status') == 'firing' and a.get('labels', {}).get('severity') == 'page':
            set_weights(100, 0)
            return {"action": "rollback"}
    return {"action": "noop"}
