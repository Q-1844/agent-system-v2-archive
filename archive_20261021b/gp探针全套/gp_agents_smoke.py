import sys, httpx
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
r = httpx.get("http://localhost:8000/api/agents", timeout=10)
print("GET /api/agents ->", r.status_code)
data = r.json()
ids = [a.get("agent_id") for a in data if isinstance(a, dict)]
print("agents:", ids[:8])
