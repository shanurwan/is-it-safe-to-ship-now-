# Canary Rollback Evidence

## What happened
- v2 was canaried (5% → 30% → 100%) under load.
- Failure was forced via `/toggle?defect=0.2&slow=1`.
- SLOs breached; controller rolled traffic back to v1.

## Proof artifacts
- `compose.logs`: shows controller logs, weights changes, and service health.
- `traefik-dynamic.yml`: final weights after rollback (expect v1=100, v2=0).
- `controller-result.txt`: "rolled back" if gate failed.
- `prom-job_http_5xx_rate.json`: 5xx rate time series (last 15 min).
- `prom-job_p95.json`: p95 latency time series (last 15 min).
- `prom-*-headline.json`: point-in-time values when captured.
- `alertmanager-alerts.json`: any active/firing SLO alerts.
- `SLO.json`: thresholds used by the gate.

## Links (local)
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090 (queries above)
- Traefik: http://localhost:8080

## Notes / takeaways
- Progressive delivery caught the issue at canary and auto-rolled back.
- Error budget kept intact; users largely shielded.
- Remediation path: `heal` and retry canary.
