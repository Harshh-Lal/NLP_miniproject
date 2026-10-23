"""Test API vs CLI parity for the M1 fixture."""
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from api.main import app
from scripts.demo_cli import FIXTURE_MESSAGE, FIXTURE_DIFF

client = TestClient(app)

# 1. Post to /audit with exact fixture
resp = client.post("/audit", json={
    "message": FIXTURE_MESSAGE,
    "diff": FIXTURE_DIFF,
})

assert resp.status_code == 200, f"Status code {resp.status_code}: {resp.text}"
api_json = resp.json()

# 2. Load CLI generated results/m1_fixture_audit.json
with open(ROOT / "results" / "m1_fixture_audit.json", "r", encoding="utf-8") as f:
    cli_json = json.load(f)

print("=== API JSON RESPONSE ===")
print(json.dumps(api_json, indent=2))
print("=" * 60)

# Check parity
if api_json == cli_json:
    print("SUCCESS: API JSON is 100% IDENTICAL to results/m1_fixture_audit.json!")
else:
    print("DIFFERENCES FOUND:")
    # Print key by key diff
    for k in set(api_json.keys()) | set(cli_json.keys()):
        v1 = api_json.get(k)
        v2 = cli_json.get(k)
        if v1 != v2:
            print(f"Key '{k}':\n  API: {v1}\n  CLI: {v2}")
