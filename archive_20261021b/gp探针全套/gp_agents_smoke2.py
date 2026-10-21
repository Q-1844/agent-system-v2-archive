import sys, httpx
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
r = httpx.get("http://localhost:8000/api/agents", timeout=10)
print("/api/agents ->", r.status_code, r.text[:200])
r2 = httpx.get("http://localhost:8000/api/agents/profiles", timeout=10)
print("/api/agents/profiles ->", r2.status_code, r2.text[:400])
