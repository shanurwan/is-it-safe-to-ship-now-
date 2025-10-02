#!/usr/bin/env bash
set -euo pipefail
python - <<'PY'
import yaml
p='/dynamic/traefik-dynamic.yml'
# in compose, mounted under rollbacker and controller; here we edit on host
p='ops/traefik/dynamic/traefik-dynamic.yml'
with open(p) as f:
  d=yaml.safe_load(f)
d['http']['services']['canary']['weighted']['services'][0]['weight']=100
d['http']['services']['canary']['weighted']['services'][1]['weight']=0
open(p,'w').write(yaml.safe_dump(d))
print('Rolled back to v1')
PY
