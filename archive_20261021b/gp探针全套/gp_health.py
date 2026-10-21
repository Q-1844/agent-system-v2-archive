import sys, httpx, io
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
r = httpx.get("http://localhost:8000/api/health", timeout=8)
print("health:", r.status_code, r.text[:120])
log = io.open(r"C:\Users\曹文淇\Desktop\ai工作流\animation-storyboard\backend_runtime.log",
              encoding="utf-8", errors="replace").read()
markers = [l for l in log.splitlines() if "launcher start" in l]
print("launcher markers:", markers[-3:])
