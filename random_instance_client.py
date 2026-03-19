import os
import random
import sys
from datetime import datetime

import requests


def discover_instances(registry_url: str, service_name: str) -> list[dict]:
    resp = requests.get(f"{registry_url}/discover/{service_name}", timeout=5)
    resp.raise_for_status()
    data = resp.json()
    return data.get("instances", [])


def call_instance(address: str, path: str) -> dict:
    url = f"{address}{path}"
    resp = requests.get(url, timeout=5)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python random_instance_client.py <service_name>")
        sys.exit(1)

    service_name = sys.argv[1]
    registry_url = os.environ.get("REGISTRY_URL", "http://localhost:5001")
    path = os.environ.get("CALL_PATH", "/ping")

    instances = discover_instances(registry_url, service_name)
    if not instances:
        print(f"[{datetime.now().isoformat()}] No instances discovered for {service_name}")
        sys.exit(1)

    chosen = random.choice(instances)
    address = chosen["address"]

    print(f"Discovered {len(instances)} instance(s) for service='{service_name}'")
    print(f"Chosen random instance address: {address}")

    result = call_instance(address, path)
    print("Response from chosen instance:")
    print(result)


if __name__ == "__main__":
    main()

# Made with Bob

