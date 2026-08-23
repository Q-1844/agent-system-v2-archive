import json, sys
from pathlib import Path
BASE = Path('.')
sys.path.insert(0, str(BASE))
from src.agents.change_protocol.store import ChangeProtocolStore
for pname, plan in (("__cancel_gp_a", "plan_cancel_a"), ("__cancel_gp_b", "plan_cancel_b")):
    s = ChangeProtocolStore(BASE / "projects" / pname, pname)
    ex = s.find_execution(plan, 1)
    print(pname, "status=", ex.status, "stage=", ex.stage, "cancel=", ex.cancel_requested,
          "synced=", [r["character_name"] for r in (ex.character_sync or [])],
          "planning=", len(ex.planning or []), "run_id=", ex.production_run_id)
