# Virtual LAN (VLAN) Configuration and Management

> **Submitted by:** [Your Name]  
> **Course:** Computer Networks / Network Administration  
> **Submission Date:** March 17, 2026

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Network Topology](#network-topology)
3. [VLAN Design](#vlan-design)
4. [Implementation Techniques](#implementation-techniques)
5. [Configuration Files](#configuration-files)
6. [Inter-VLAN Routing](#inter-vlan-routing)
7. [Scripts & Tools](#scripts--tools)
8. [Testing & Verification](#testing--verification)
9. [Security Considerations](#security-considerations)
10. [Concepts Summary](#concepts-summary)

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

## Configuration Files

All device configurations are in the [`configs/`](configs/) directory:

```
configs/
├── switches/
│   ├── core-switch.cfg        # Core L3 switch with SVIs
│   ├── sw-a-sales.cfg         # Access switch – Sales VLAN
│   ├── sw-b-finance.cfg       # Access switch – Finance VLAN
│   └── sw-c-it.cfg            # Access switch – IT VLAN
└── routers/
    ├── router-roas.cfg        # Router-on-a-Stick configuration
    └── router-acl.cfg         # ACL rules for inter-VLAN filtering
```

---

## Inter-VLAN Routing

### Routing Table (Core Switch)

```
C  10.10.10.0/24  [directly connected, Vlan10]
C  10.20.20.0/24  [directly connected, Vlan20]
C  10.30.30.0/24  [directly connected, Vlan30]
S  0.0.0.0/0      [via 192.168.0.1]
```

### Communication Matrix

| Source VLAN | Destination VLAN | Allowed | Notes |
|-------------|------------------|---------|-------|
| SALES (10) | FINANCE (20) | ❌ No | Blocked by ACL |
| SALES (10) | IT (30) | ✅ Yes | Help desk access |
| FINANCE (20) | IT (30) | ✅ Yes | IT support |
| FINANCE (20) | SALES (10) | ❌ No | Blocked by ACL |
| IT (30) | All VLANs | ✅ Yes | Full admin access |

---

## Scripts & Tools

### Python VLAN Manager (`scripts/vlan_manager.py`)

A CLI utility for simulating VLAN operations and generating configuration commands:

```bash
# Show all VLANs
python scripts/vlan_manager.py --list

# Add a new VLAN
python scripts/vlan_manager.py --add --id 50 --name HR --subnet 10.50.50.0/24

# Generate switch config for a VLAN
python scripts/vlan_manager.py --generate --id 10 --device SW-A --ports fa0/1,fa0/2

# Verify VLAN connectivity (simulated ping)
python scripts/vlan_manager.py --verify --src 10 --dst 30
```

### Verification Script (`scripts/verify_vlans.sh`)

Bash script that connects to network devices (via SSH) and runs `show` commands to verify the VLAN configuration is applied correctly.

---

## Testing & Verification

### Verification Commands

After applying configurations, use these Cisco IOS commands to verify:

```bash
# Show all VLANs configured on a switch
show vlan brief

# Verify trunk ports and allowed VLANs
show interfaces trunk

# Check SVI status on Layer 3 switch
show ip interface brief

# Inspect routing table
show ip route

# Test inter-VLAN connectivity
ping 10.20.20.10 source vlan 10

# Show port security status
show port-security interface fa0/1

# Check VTP status
show vtp status
```

### Expected Test Results

| Test | Command | Expected Result |
|------|---------|-----------------|
| VLAN 10 → VLAN 30 | ping 10.30.30.10 source vlan10 | Success (5/5 packets) |
| VLAN 10 → VLAN 20 | ping 10.20.20.10 source vlan10 | Fail (ACL deny) |
| Trunk status | show interfaces trunk | Gi0/1 trunking, VLANs 10,20,30,40 |
| SVI status | show ip int brief | Vlan10/20/30/40 up/up |

---

## Security Considerations

### Port Security

Configured on all access ports to prevent MAC flooding and unauthorized device connections:

- Maximum 2 MAC addresses per port
- Violation mode: `shutdown` (port disabled on violation)
- Sticky MAC learning enabled

### VLAN Hopping Prevention

Double-tagging and switch spoofing attacks are mitigated by:

1. Setting all unused ports to access mode and assigning to an unused VLAN (VLAN 999)
2. Disabling DTP (Dynamic Trunking Protocol) on access ports: `switchport nonegotiate`
3. Using a non-default native VLAN (VLAN 99) on all trunk links
4. Pruning unused VLANs from trunk links

### Access Control Lists (ACLs)

Extended ACLs applied on the core switch SVIs control inter-VLAN communication as per the communication matrix above.

---

## Concepts Summary

| Concept | Definition |
|---------|-----------|
| **VLAN** | A logical network segment independent of physical topology |
| **802.1Q** | IEEE standard for VLAN tagging on Ethernet frames |
| **Trunk Port** | A port carrying traffic from multiple VLANs using 802.1Q tags |
| **Access Port** | A port belonging to exactly one VLAN; connects end devices |
| **SVI** | Switch Virtual Interface — a Layer 3 interface bound to a VLAN |
| **ROAS** | Router-on-a-Stick — inter-VLAN routing via sub-interfaces |
| **VTP** | VLAN Trunking Protocol — Cisco proprietary VLAN database sync |
| **Native VLAN** | The untagged VLAN on a trunk link (default: VLAN 1) |
| **DTP** | Dynamic Trunking Protocol — auto-negotiates trunk links |

---

## References

- Cisco IOS Documentation — VLAN Configuration Guide
- IEEE 802.1Q Standard — Virtual Bridged Local Area Networks
- Odom, W. (2020). *CCNA 200-301 Official Cert Guide*. Cisco Press.
- Tanenbaum, A. & Wetherall, D. (2021). *Computer Networks* (6th ed.). Pearson.

---

*Project files tested in Cisco Packet Tracer 8.2 and GNS3 2.2.*
