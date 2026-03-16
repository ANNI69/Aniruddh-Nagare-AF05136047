# Virtual LAN (VLAN) Configuration and Management

> **Submitted by:** Aniruddh Deepak Nagare  
> **Course:** ANP-D2217-NCS  
> **Submission Date:** March 17, 2026

---


## Project Overview

This project demonstrates the complete lifecycle of Virtual LAN (VLAN) configuration and management on a simulated enterprise network. VLANs allow a single physical network to be logically divided into multiple isolated broadcast domains, delivering three core benefits:

- **Security** — Isolate sensitive departments (e.g., Finance, HR) from general users
- **Performance** — Reduce broadcast traffic by limiting it to relevant segments
- **Manageability** — Simplify administration by grouping users by function rather than location

### Techniques Covered

| Technique | Description |
|-----------|-------------|
| VLAN creation and naming | Assigning VLAN IDs (1–4094) and human-readable names |
| Access port assignment | Binding end-device ports to a single VLAN |
| Trunk port configuration | Carrying multiple VLANs over inter-switch links using 802.1Q |
| Router-on-a-Stick (ROAS) | Inter-VLAN routing via sub-interfaces on a Layer 3 router |
| Layer 3 Switch Routing | Inter-VLAN routing using SVIs on a multilayer switch |
| VTP (VLAN Trunking Protocol) | Propagating VLAN configurations across multiple switches |
| Port Security | Restricting access-port connections by MAC address |

---

## Network Topology

```
                         INTERNET
                             |
                        [ Router0 ]
                        192.168.0.1
                             |  (Trunk: all VLANs)
                      [ Core Switch ]
                      (Layer 3 / SVI)
                      /      |      \
             (Trunk) /    (Trunk)    \ (Trunk)
                    /        |        \
              [SW-A]       [SW-B]     [SW-C]
           (Access)      (Access)   (Access)
              |              |           |
         VLAN 10         VLAN 20     VLAN 30
          (Sales)       (Finance)     (IT)
         10.10.10.x     10.20.20.x   10.30.30.x
```

### Device Inventory

| Device | Role | Management IP |
|--------|------|--------------|
| Router0 | Gateway / ROAS | 192.168.0.1 |
| Core-SW | Layer 3 Switch | 192.168.0.2 |
| SW-A | Access Switch – Sales | 192.168.0.10 |
| SW-B | Access Switch – Finance | 192.168.0.11 |
| SW-C | Access Switch – IT | 192.168.0.12 |

---

## VLAN Design

| VLAN ID | Name | Subnet | Gateway | Purpose |
|---------|------|--------|---------|---------|
| 10 | SALES | 10.10.10.0/24 | 10.10.10.1 | Sales department |
| 20 | FINANCE | 10.20.20.0/24 | 10.20.20.1 | Finance department |
| 30 | IT | 10.30.30.0/24 | 10.30.30.1 | IT / Admin staff |
| 40 | MANAGEMENT | 192.168.0.0/24 | 192.168.0.1 | Switch management |
| 99 | NATIVE | — | — | Untagged trunk traffic |

> **Best Practice:** VLAN 1 is never used for production traffic. A dedicated management VLAN (40) is used for switch administration.

---

## Implementation Techniques

### Technique 1 — Router-on-a-Stick (ROAS)

One physical router interface is divided into logical **sub-interfaces**, each tagged with a VLAN ID using IEEE 802.1Q encapsulation. The router performs routing between VLANs.

```
Router Fa0/0
├── Fa0/0.10  → VLAN 10  (10.10.10.1/24)
├── Fa0/0.20  → VLAN 20  (10.20.20.1/24)
└── Fa0/0.30  → VLAN 30  (10.30.30.1/24)
```

**Pros:** Cost-effective (single router interface), easy to implement.  
**Cons:** Single point of failure; physical link can become a bottleneck at high traffic.

---

### Technique 2 — Layer 3 Switch with SVIs

A **Switched Virtual Interface (SVI)** is a virtual Layer 3 interface on the switch tied to a VLAN. The switch itself routes between VLANs without a separate router for inter-VLAN traffic.

```
Core-SW
├── VLAN 10 SVI: 10.10.10.1/24
├── VLAN 20 SVI: 10.20.20.1/24
└── VLAN 30 SVI: 10.30.30.1/24
```

**Pros:** High throughput (hardware-based routing), no external router needed.  
**Cons:** More expensive than unmanaged switches; requires multilayer switch.

---


### Communication Matrix

| Source VLAN | Destination VLAN | Allowed | Notes |
|-------------|------------------|---------|-------|
| SALES (10) | FINANCE (20) | ❌ No | Blocked by ACL |
| SALES (10) | IT (30) | ✅ Yes | Help desk access |
| FINANCE (20) | IT (30) | ✅ Yes | IT support |
| FINANCE (20) | SALES (10) | ❌ No | Blocked by ACL |
| IT (30) | All VLANs | ✅ Yes | Full admin access |

---
