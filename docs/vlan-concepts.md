# VLAN Concepts & Theory

## What is a VLAN?

A **Virtual Local Area Network (VLAN)** is a logical grouping of network devices
regardless of their physical location. Devices in the same VLAN communicate as if
they are connected to the same physical switch, even if they are on different switches
or floors of a building.

---

## How 802.1Q Tagging Works

IEEE 802.1Q is the standard for VLAN tagging. When a frame crosses a trunk link,
a 4-byte tag is inserted into the Ethernet header:

```
Original Ethernet Frame:
┌──────────┬────────┬──────┬──────────────────┬─────┐
│ Dst MAC  │Src MAC │ Type │    Payload       │ FCS │
└──────────┴────────┴──────┴──────────────────┴─────┘

802.1Q Tagged Frame:
┌──────────┬────────┬───────────────┬──────┬──────────────────┬─────┐
│ Dst MAC  │Src MAC │  802.1Q Tag   │ Type │    Payload       │ FCS │
│          │        │ (4 bytes)     │      │                  │     │
└──────────┴────────┴───────────────┴──────┴──────────────────┴─────┘
                     ↓
              ┌─────────────────┐
              │  TPID (2 bytes) │  = 0x8100 (identifies 802.1Q frame)
              │  TCI  (2 bytes) │
              │  ├─ PCP (3 bits)│  Priority Code Point (QoS)
              │  ├─ DEI (1 bit) │  Drop Eligible Indicator
              │  └─ VID (12bits)│  VLAN ID (0–4095)
              └─────────────────┘
```

The 12-bit VLAN ID supports **4,096 VLANs** (IDs 0–4095).
- VLAN 0 and 4095 are reserved.
- VLAN 1 is the default (not recommended for production).
- Usable range: **2–4094**.

---

## Port Types

### Access Port
- Belongs to **exactly one VLAN**
- Connects end devices (PCs, printers, phones)
- Frames are **untagged** on the wire
- Switch adds/removes the VLAN tag internally

```
PC ──────(untagged)──── Access Port [VLAN 10] ──── Switch
```

### Trunk Port
- Carries **multiple VLANs**
- Connects switch-to-switch or switch-to-router
- Frames are **tagged** with 802.1Q headers
- Native VLAN traffic is sent untagged

```
Switch A ──(tagged: VLAN 10,20,30)── Trunk Port ──── Switch B
```

---

## Inter-VLAN Routing Methods

### Method 1: Router-on-a-Stick

```
        Router
        Fa0/0 (physical)
          │
          ├── Fa0/0.10 — encapsulation dot1Q 10 — 10.10.10.1/24
          ├── Fa0/0.20 — encapsulation dot1Q 20 — 10.20.20.1/24
          └── Fa0/0.30 — encapsulation dot1Q 30 — 10.30.30.1/24
          │
       (single trunk cable)
          │
       Switch Gi0/1 (trunk)
```

**Traffic flow** (PC in VLAN 10 pings PC in VLAN 20):
1. PC10 sends frame to its default gateway (10.10.10.1)
2. Switch tags frame with VLAN 10 and forwards up trunk
3. Router receives on Fa0/0.10, strips tag, routes to VLAN 20
4. Router sends frame back down trunk, tagged with VLAN 20
5. Switch strips VLAN 20 tag, delivers to destination PC

**Limitation:** All inter-VLAN traffic goes up and back on the same physical link (hairpin). This can create a bottleneck on high-traffic networks.

### Method 2: Layer 3 Switch with SVIs

```
Layer 3 Switch
├── Vlan10 SVI: 10.10.10.1/24   (virtual L3 interface)
├── Vlan20 SVI: 10.20.20.1/24
└── Vlan30 SVI: 10.30.30.1/24
```

**Traffic flow** (PC in VLAN 10 pings PC in VLAN 20):
1. PC10 sends frame to default gateway (10.10.10.1 = Vlan10 SVI)
2. Switch receives on VLAN 10, routes in hardware to VLAN 20 SVI
3. Switch delivers frame directly to destination (no external router needed)

**Advantage:** Routing is performed in dedicated ASICs at wire speed — much faster than ROAS.

---

## VTP (VLAN Trunking Protocol)

VTP is a Cisco proprietary protocol that synchronises the VLAN database across all switches in a domain.

| Mode | Behaviour |
|------|-----------|
| **Server** | Can create/modify/delete VLANs. Advertises to domain. |
| **Client** | Receives VLANs from server. Cannot create VLANs locally. |
| **Transparent** | Does not participate in VTP. Forwards VTP advertisements. |
| **Off** | Does not send or forward VTP advertisements. |

**VTP Domain:** A group of switches sharing VLAN information.  
**VTP Password:** Prevents unauthorised switches from joining the domain.

> **Warning:** Adding a switch with a higher VTP revision number to a domain will overwrite the VLAN database on all switches. Always set new switches to VTP transparent before adding to a production network.

---

## VLAN Security

### VLAN Hopping Attacks

**Attack 1: Switch Spoofing**
An attacker configures their NIC to negotiate a trunk link, gaining access to all VLANs.

**Mitigation:**
```
interface fa0/1
 switchport mode access        ← force access mode
 switchport nonegotiate        ← disable DTP
```

**Attack 2: Double Tagging**
An attacker adds two 802.1Q tags. The first switch strips the outer tag; the inner tag carries the frame to a second VLAN.

**Mitigation:**
- Change the native VLAN to an unused VLAN (not VLAN 1):
  ```
  switchport trunk native vlan 99
  ```
- Explicitly tag all native VLAN traffic:
  ```
  vlan dot1q tag native
  ```

### Port Security

Limits the number of MAC addresses that can connect to a port.

```
switchport port-security                        ← enable
switchport port-security maximum 1              ← max MACs
switchport port-security mac-address sticky     ← learn dynamically
switchport port-security violation shutdown     ← shut port on violation
```

**Violation modes:**

| Mode | Behaviour | Increments Counter | Sends Syslog |
|------|-----------|-------------------|--------------|
| shutdown | Port disabled (err-disabled) | Yes | Yes |
| restrict | Drops frames, port stays up | Yes | Yes |
| protect | Drops frames silently | No | No |

---

## Spanning Tree Protocol (STP)

STP prevents Layer 2 loops in networks with redundant paths.

| Protocol | Standard | Convergence |
|----------|----------|------------|
| STP | IEEE 802.1D | ~30–50 sec |
| RSTP | IEEE 802.1w | ~1–2 sec |
| Rapid PVST+ | Cisco (802.1w per-VLAN) | ~1–2 sec |

**PortFast:** Skips STP listening/learning on access ports connected to end devices.
**BPDU Guard:** Shuts down a PortFast port if a BPDU (switch hello) is received, preventing unauthorised switches.

```
spanning-tree portfast            ← on access ports
spanning-tree bpduguard enable    ← on access ports
```
