# Assignment Architecture Diagram (Service Discovery + Random Call)

## Mandatory Part (Custom Service Registry)

```mermaid
flowchart LR
  subgraph Registry["Service Registry (Flask)"]
    A1["POST /register"]
    A2["POST /heartbeat"]
    A3["GET /discover/<service>"]
  end

  subgraph Service["Two instances of the same microservice"]
    S1["user-service @ :8001"]
    S2["user-service @ :8002"]
  end

  subgraph Client["Client App"]
    C1["Discover instances"]
    C2["Pick random instance"]
    C3["Call /ping on chosen instance"]
  end

  S1 -->|register + heartbeat| A1
  S2 -->|register + heartbeat| A1
  C1 -->|GET /discover/user-service| A3
  A3 --> C2
  C2 -->|GET http://:800x/ping| S1
  C2 -->|GET http://:800x/ping| S2
```

## Optional Part (Service Mesh Discovery in Kubernetes)

The app can call the Kubernetes `Service` (e.g., `http://user-service:8001/ping`) and the sidecar proxy (Envoy for Istio) does load balancing/routing across pods.

```mermaid
flowchart LR
  App["App"] --> Sidecar["Sidecar Proxy"]
  Sidecar --> Mesh["Service Mesh (Istio/Linkerd)"]
  Mesh --> Pod1["user-service pod #1"]
  Mesh --> Pod2["user-service pod #2"]
```

