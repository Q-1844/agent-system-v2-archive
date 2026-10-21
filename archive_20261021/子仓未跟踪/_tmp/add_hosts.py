# _tmp/add_hosts.py — 以管理员写入 hosts（api.agnes-ai.cn DNS 污染恢复）
import subprocess
line = "111.7.87.222 api.agnes-ai.cn"
ps = ("Start-Process powershell -Verb RunAs -Wait -ArgumentList "
      "'-Command Add-Content -Path C:\\Windows\\System32\\drivers\\etc\\hosts -Value \"\\n" + line + "\"'")
r = subprocess.run(["powershell", "-Command", ps], capture_output=True, text=True, timeout=90)
print("rc=", r.returncode)
if r.stderr:
    print("err:", r.stderr[:300])
