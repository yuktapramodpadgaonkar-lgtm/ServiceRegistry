import os
import signal
import sys
import socket
import threading
import time
from datetime import datetime

import requests
from flask import Flask, jsonify


app = Flask(__name__)


def _safe_post(url: str, payload: dict, timeout_s: float = 5.0) -> requests.Response:
    return requests.post(url, json=payload, timeout=timeout_s)


def _get_env(name: str, default: str) -> str:
    return os.environ.get(name, default)


def create_app(service_name: str, port: int, instance_id: str):
    @app.route("/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

    @app.route("/ping", methods=["GET"])
    def ping():
        return jsonify(
            {
                "service": service_name,
                "instance_id": instance_id,
                "port": port,
                "timestamp": datetime.now().isoformat(),
            }
        )


def run_microservice(service_name: str, port: int):
    registry_url = _get_env("REGISTRY_URL", "http://localhost:5001")
    pod_ip = os.environ.get("POD_IP")  # set in Kubernetes
    instance_id = os.environ.get("INSTANCE_ID")

    if not instance_id:
        instance_id = f"{socket.gethostname()}:{port}"

    # Address that we register with the registry. In Kubernetes, use POD_IP; locally, default to localhost.
    if os.environ.get("SERVICE_ADDRESS"):
        service_address = os.environ["SERVICE_ADDRESS"]
    elif pod_ip:
        service_address = f"http://{pod_ip}:{port}"
    else:
        service_address = f"http://localhost:{port}"

    create_app(service_name=service_name, port=port, instance_id=instance_id)

    stop_event = threading.Event()

    def register() -> None:
        payload = {"service": service_name, "address": service_address}
        _safe_post(f"{registry_url}/register", payload)

    def deregister() -> None:
        payload = {"service": service_name, "address": service_address}
        try:
            _safe_post(f"{registry_url}/deregister", payload)
        except Exception:
            # During shutdown, the registry might already be down; don't crash the process.
            pass

    def heartbeat_loop() -> None:
        # Heartbeat frequency is aligned with the README (10s).
        interval_s = float(_get_env("HEARTBEAT_INTERVAL_S", "10"))
        while not stop_event.is_set():
            payload = {"service": service_name, "address": service_address}
            try:
                _safe_post(f"{registry_url}/heartbeat", payload)
            except Exception:
                # Keep running; registry will eventually time out if needed.
                pass
            stop_event.wait(interval_s)

    # Initial registration + background heartbeat.
    register()
    threading.Thread(target=heartbeat_loop, daemon=True).start()

    def shutdown_handler(signum, frame):
        stop_event.set()
        deregister()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    # Serve HTTP for the client to call.
    app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False, threaded=True)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python microservice_instance.py <service_name> <port>")
        sys.exit(1)

    service_name_arg = sys.argv[1]
    port_arg = int(sys.argv[2])
    run_microservice(service_name=service_name_arg, port=port_arg)

# Made with Bob

