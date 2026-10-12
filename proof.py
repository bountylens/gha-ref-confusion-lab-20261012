import hashlib
import json
import os
import subprocess


canary = os.environ["CONTROLLED_CANARY"]
checked_out_sha = subprocess.check_output(
    ["git", "rev-parse", "HEAD"], text=True
).strip()

proof = {
    "marker": "external-fork-script-executed",
    "canary_sha256": hashlib.sha256(canary.encode()).hexdigest(),
    "checked_out_sha": checked_out_sha,
    "api_head_sha": os.environ["EXPECTED_HEAD_SHA"],
    "api_head_repo": os.environ["EXPECTED_HEAD_REPO"],
}

with open("proof.json", "w", encoding="utf-8") as handle:
    json.dump(proof, handle, indent=2, sort_keys=True)
    handle.write("\n")

print(json.dumps(proof, sort_keys=True))
