I will recreate the architecture diagram using Mermaid in Markdown.

The diagram will be structured as a **Flowchart (Top-Down within IDC, Left-Right overall)** to match the visual flow.

### Diagram Structure:

1.  **External / User Layer**:
    *   **User**: The starting point.
    *   **Gaeadns**: DNS resolution service.
    *   **Flow**: User requests domain -> Gaeadns returns IP -> User connects to HK Entry.

2.  **Cross-Border Link**:
    *   **Hong Kong (HK)**: Tencent Cloud GAAP HK Entrance (IP: 101.32.16.227).
    *   **Connection**: Tencent Cloud Internal Private Line.
    *   **Mainland (GZ)**: Tencent Cloud GAAP GZ Exit.

3.  **Domestic IDC (Mainland)**:
    *   **Entry Point**: Origin IP (14.119.64.135, Ports 8080/8081). Connection uses Proxy Protocol.
    *   **Layer 1 (L1) - Ingress Gateways**:
        *   `gd16-vgw` cluster (Telecom/Unicom/Mobile).
        *   `gd15-vgw` cluster (CT/CU/CM).
    *   **Layer 2 (L2) - Nginx Proxies**:
        *   `gd16-nginx-external-customize`.
        *   `gd15-nginx-external-customize`.
    *   **Layer 3 (L3) - Service Gateways & Routing**:
        *   We will map the 4 distinct color-coded paths from the diagram:
            *   **Green Path**: Targeted at `mapi.vipglobal.hk`.
            *   **Pink Path**: Targeted at `mar.vipglobal.hk`.
            *   **Black Path**: Targeted at `www.vipglobal.hk` / `m.vipglobal.hk`.
            *   **Cyan Path**: Targeted at `vop.vipglobal.hk`.
    *   **Layer 4 (L4) - Application Clusters**:
        *   Janus Clusters (0001, Mars, 0101) and HAProxy.
    *   **Layer 5 (L5) - Domains**:
        *   Final destination domains.

### Implementation Details:
-   I will use `flowchart TB` (Top-Bottom) inside the IDC subgraph for better layout.
-   I will use `subgraph` to visually group Hong Kong, Mainland, and the IDC layers.
-   I will use Mermaid classes and `linkStyle` to represent the colored paths (Green, Pink, Black, Cyan) for clarity.
