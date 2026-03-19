import os
import sys
import time
from datetime import datetime

import requests


def main() -> None:
    # In Kubernetes with a service mesh, this URL (service DNS) will be routed by the mesh.
    target_url = os.environ.get("TARGET_URL", "http://user-service:8001/ping")
    iterations = int(os.environ.get("ITERATIONS", "5"))
    sleep_s = float(os.environ.get("SLEEP_S", "1"))

    print(f"Mesh client starting. target_url={target_url} iterations={iterations}")

    for i in range(iterations):
        resp = requests.get(target_url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        print(f"[{datetime.now().isoformat()}] call #{i+1} -> instance_id={data.get('instance_id')} payload={data}")
        time.sleep(sleep_s)


if __name__ == "__main__":
    # Optional: allow overriding iterations via CLI.
    if len(sys.argv) > 1:
        os.environ["ITERATIONS"] = sys.argv[1]
    main()

# Made with Bob

