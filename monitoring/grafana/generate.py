import json

P = {"type": "prometheus", "uid": "${ds_prom}"}
L = {"type": "loki", "uid": "${ds_loki}"}

def var(name, query, label):
    return {"name": name, "label": label, "type": "datasource",
            "query": query, "current": {}, "hide": 0}

def panel(i, title, typ, x, y, w, h, ds, exprs, **kw):
    targets = [{"refId": chr(65 + n), "expr": e, "legendFormat": lf, "datasource": ds}
               for n, (e, lf) in enumerate(exprs)]
    p = {"id": i, "title": title, "type": typ, "datasource": ds,
         "gridPos": {"x": x, "y": y, "w": w, "h": h}, "targets": targets}
    p.update(kw)
    return p

def dash(uid, title, variables, panels):
    return {"uid": uid, "title": title, "schemaVersion": 39, "version": 1,
            "refresh": "30s", "time": {"from": "now-1h", "to": "now"},
            "templating": {"list": variables}, "panels": panels}

def unit(u):
    return {"defaults": {"unit": u}, "overrides": []}

NS = 'namespace="parcial-ricj", container!=""'
metrics = dash("cluster-metrics", "Cluster Metrics (ricj)", [var("ds_prom", "prometheus", "Prometheus")], [
    panel(1, "Node CPU usage (%)", "timeseries", 0, 0, 12, 8, P,
          [('100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)', "CPU %")],
          fieldConfig=unit("percent")),
    panel(2, "Node memory usage (%)", "timeseries", 12, 0, 12, 8, P,
          [('100 * (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)', "Memory %")],
          fieldConfig=unit("percent")),
    panel(3, "Running pods", "stat", 0, 8, 6, 6, P,
          [('sum(kube_pod_status_phase{phase="Running"})', "Running")]),
    panel(4, "Pods by phase", "timeseries", 6, 8, 18, 6, P,
          [('sum by (phase) (kube_pod_status_phase)', "{{phase}}")]),
    panel(5, "CPU by pod (parcial-ricj)", "timeseries", 0, 14, 12, 8, P,
          [('sum by (pod) (rate(container_cpu_usage_seconds_total{%s}[5m]))' % NS, "{{pod}}")]),
    panel(6, "Memory by pod (parcial-ricj)", "timeseries", 12, 14, 12, 8, P,
          [('sum by (pod) (container_memory_working_set_bytes{%s})' % NS, "{{pod}}")],
          fieldConfig=unit("bytes")),
])

apps = ["app-nginx", "app-httpd", "app-whoami", "app-echo"]
panels = [panel(1, "Log volume per app", "timeseries", 0, 0, 24, 7, L,
                [('sum by (app) (count_over_time({namespace=~"parcial-ricj|traefik"}[1m]))', "{{app}}")])]
y = 7
for n, a in enumerate(apps + ["traefik"]):
    sel = '{namespace="traefik"}' if a == "traefik" else '{namespace="parcial-ricj", app="%s"}' % a
    panels.append(panel(n + 2, "Logs: " + a, "logs", 0 if n % 2 == 0 else 12, y, 12, 8, L,
                        [(sel, "")], options={"showTime": True, "sortOrder": "Descending"}))
    if n % 2 == 1:
        y += 8
logs = dash("app-logs", "Application Logs (ricj)", [var("ds_loki", "loki", "Loki")], panels)

for name, d in (("cluster-metrics", metrics), ("app-logs", logs)):
    with open("monitoring/grafana/dashboards/%s.json" % name, "w") as f:
        json.dump(d, f, indent=2)
print("OK")
