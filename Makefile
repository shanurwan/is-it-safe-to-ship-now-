SHELL := /bin/bash

.PHONY: bootstrap up down teardown traffic stop-traffic canary promote rollback fail heal policy plan apply destroy ci-act

bootstrap:
	@echo "Pulling images & validating..."
	docker pull traefik:v3.1 || true
	docker pull prom/prometheus:v2.55.0 || true
	docker pull grafana/grafana:11.1.4 || true
	docker pull prom/alertmanager:v0.27.0 || true

up:
	docker compose up -d traefik prometheus alertmanager grafana api-v1

down:
	docker compose down

teardown:
	docker compose down -v --rmi local --remove-orphans || true

traffic:
	docker compose up -d traffic

stop-traffic:
	docker compose rm -sf traffic || true

canary:
	docker compose up -d api-v2
	docker compose run --rm canary-controller python /app/controller.py

promote:
	python - <<-'PY'
	import yaml
	p = 'ops/traefik/dynamic/traefik-dynamic.yml'
	with open(p, 'r') as f:
	    d = yaml.safe_load(f)
	d['http']['services']['canary']['weighted']['services'][0]['weight'] = 0
	d['http']['services']['canary']['weighted']['services'][1]['weight'] = 100
	with open(p, 'w') as f:
	    yaml.safe_dump(d, f, sort_keys=False)
	print('Promoted v2 100%')
	PY


rollback:
	bash ci/scripts/rollback.sh

fail:
	@curl -s 'http://localhost/toggle?defect=0.2&slow=1' || true

heal:
	@curl -s 'http://localhost/toggle?defect=0.0&slow=0' || true

policy:
	docker run --rm -v "$$(pwd):/repo" bridgecrew/checkov checkov -d /repo || true
	docker run --rm -v "$$(pwd):/project" openpolicyagent/conftest conftest test /project/infra || true
	docker run --rm -v "$$(pwd):/repo" aquasec/trivy:0.53.0 fs /repo || true
	docker run --rm -v "$$(pwd):/repo" zricethezav/gitleaks:latest detect --no-git -s /repo || true

plan:
	cd infra && terraform fmt -recursive && terraform init && terraform validate && terraform plan -out=tfplan || true

apply:
	cd infra && terraform apply -auto-approve tfplan || true

destroy:
	cd infra && terraform destroy -auto-approve || true

ci-act:
	act -W .github/workflows/deploy.yml -j deploy || true
