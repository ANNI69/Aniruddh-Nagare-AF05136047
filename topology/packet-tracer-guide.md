# Cisco Packet Tracer – Lab Setup Guide

## Topology to Build

This guide walks you through recreating the VLAN lab in **Cisco Packet Tracer 8.2**.

---

## Step 1: Place Devices

From the device panel, drag and drop:

| Qty | Device | Model |
|-----|--------|-------|
| 1 | Router | Cisco ISR 4321 (or 2901) |
| 1 | Switch | Cisco 3650-24PS (Layer 3) |
| 3 | Switch | Cisco 2960-24TT (Layer 2) |
| 6 | PC | Generic PC-PT |

---

## Step 2: Connect Devices

Use **Copper Straight-Through** cables:

```
Router0  Gi0/0/0  ───────  Core-SW  Gi1/0/1
Core-SW  Gi1/0/2  ───────  SW-A     Gi0/1
Core-SW  Gi1/0/3  ───────  SW-B     Gi0/1
Core-SW  Gi1/0/4  ───────  SW-C     Gi0/1

SW-A    Fa0/1    ───────  PC-Sales-1
SW-A    Fa0/2    ───────  PC-Sales-2
SW-B    Fa0/1    ───────  PC-Finance-1
SW-B    Fa0/2    ───────  PC-Finance-2
SW-C    Fa0/1    ───────  PC-IT-1
SW-C    Fa0/2    ───────  PC-IT-2
```

---

## Step 3: Apply Configurations

Click each device → **CLI** tab → paste configs from `configs/` directory.

**Order matters:**
1. Core-SW first (creates VLANs in VTP server mode)
2. SW-A, SW-B, SW-C (receive VLANs from VTP)
3. Router0 last (sub-interfaces depend on switch trunks being up)

---

## Step 4: Configure PC IP Addresses

| PC | IP Address | Subnet Mask | Default Gateway |
|----|-----------|-------------|-----------------|
| PC-Sales-1 | 10.10.10.11 | 255.255.255.0 | 10.10.10.1 |
| PC-Sales-2 | 10.10.10.12 | 255.255.255.0 | 10.10.10.1 |
| PC-Finance-1 | 10.20.20.11 | 255.255.255.0 | 10.20.20.1 |
| PC-Finance-2 | 10.20.20.12 | 255.255.255.0 | 10.20.20.1 |
| PC-IT-1 | 10.30.30.11 | 255.255.255.0 | 10.30.30.1 |
| PC-IT-2 | 10.30.30.12 | 255.255.255.0 | 10.30.30.1 |

---

## Step 5: Run Verification Tests

### Test A: Same-VLAN Communication (should work)
```
PC-Sales-1> ping 10.10.10.12
```
Expected: Reply from 10.10.10.12 ✔

### Test B: IT can reach all VLANs (should work)
```
PC-IT-1> ping 10.10.10.11
PC-IT-1> ping 10.20.20.11
```
Expected: Both succeed ✔

### Test C: Sales CANNOT reach Finance (ACL blocks)
```
PC-Sales-1> ping 10.20.20.11
```
Expected: Request timeout (5 packets, 0 replies) ✔

### Test D: Finance CANNOT reach Sales (ACL blocks)
```
PC-Finance-1> ping 10.10.10.11
```
Expected: Request timeout ✔

---

## Step 6: Use Simulation Mode

1. Switch Packet Tracer to **Simulation Mode** (bottom right)
2. Create a PDU from PC-Sales-1 to PC-IT-1
3. Press **Play** to step through each hop
4. Observe:
   - 802.1Q tags added/removed at access ports
   - VLAN tag on trunk link
   - Routing decision at Core-SW or Router SVI
   - Tag changed for VLAN 30 on egress

---

## Saving Your Lab

Save the `.pkt` file as:
```
topology/vlan-lab-complete.pkt
```

Take screenshots of:
- `show vlan brief` output on Core-SW
- `show interfaces trunk` on Core-SW
- Successful ping from IT → Sales
- Failed ping from Sales → Finance
