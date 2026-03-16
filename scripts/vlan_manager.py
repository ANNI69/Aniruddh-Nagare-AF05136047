#!/usr/bin/env python3
"""
VLAN Configuration Manager
===========================
A CLI utility for managing VLAN configurations,
generating Cisco IOS commands, and simulating
connectivity verification.

Usage:
    python vlan_manager.py --list
    python vlan_manager.py --add --id 50 --name HR --subnet 10.50.50.0/24
    python vlan_manager.py --generate --id 10 --device SW-A --ports fa0/1,fa0/2
    python vlan_manager.py --verify --src 10 --dst 30
    python vlan_manager.py --topology

Project: VLAN Configuration and Management
"""

import argparse
import json
import ipaddress
from datetime import datetime

# ──────────────────────────────────────────────────────────────────
# VLAN Database (simulates a persistent store)
# ──────────────────────────────────────────────────────────────────

VLAN_DB = {
    10: {
        "name": "SALES",
        "subnet": "10.10.10.0/24",
        "gateway": "10.10.10.1",
        "description": "Sales department workstations",
        "color": "\033[32m",   # green
    },
    20: {
        "name": "FINANCE",
        "subnet": "10.20.20.0/24",
        "gateway": "10.20.20.1",
        "description": "Finance department (restricted)",
        "color": "\033[33m",   # yellow
    },
    30: {
        "name": "IT",
        "subnet": "10.30.30.0/24",
        "gateway": "10.30.30.1",
        "description": "IT admin – full access",
        "color": "\033[34m",   # blue
    },
    40: {
        "name": "MANAGEMENT",
        "subnet": "192.168.0.0/24",
        "gateway": "192.168.0.1",
        "description": "Switch/router management",
        "color": "\033[35m",   # magenta
    },
    99: {
        "name": "NATIVE",
        "subnet": "N/A",
        "gateway": "N/A",
        "description": "Untagged trunk traffic",
        "color": "\033[90m",   # dark gray
    },
}

# Communication policy: (src, dst) → allowed?
ACL_POLICY = {
    (10, 20): False,   # Sales → Finance: BLOCKED
    (20, 10): False,   # Finance → Sales: BLOCKED
    (10, 30): True,    # Sales → IT: allowed
    (20, 30): True,    # Finance → IT: allowed
    (30, 10): True,    # IT → Sales: allowed (admin)
    (30, 20): True,    # IT → Finance: allowed (admin)
}

RESET = "\033[0m"
BOLD  = "\033[1m"
RED   = "\033[31m"
GREEN = "\033[32m"

# ──────────────────────────────────────────────────────────────────
# Helper functions
# ──────────────────────────────────────────────────────────────────

def print_header(title: str) -> None:
    width = 60
    print(f"\n{BOLD}{'─' * width}")
    print(f"  {title}")
    print(f"{'─' * width}{RESET}\n")


def list_vlans() -> None:
    """Display a formatted table of all configured VLANs."""
    print_header("Configured VLANs")
    header = f"{'VLAN ID':<10}{'Name':<14}{'Subnet':<20}{'Gateway':<16}{'Description'}"
    print(f"{BOLD}{header}{RESET}")
    print("─" * 78)
    for vlan_id in sorted(VLAN_DB.keys()):
        v = VLAN_DB[vlan_id]
        color = v.get("color", "")
        print(
            f"{color}{vlan_id:<10}{v['name']:<14}{v['subnet']:<20}"
            f"{v['gateway']:<16}{v['description']}{RESET}"
        )
    print(f"\nTotal VLANs: {len(VLAN_DB)}")


def add_vlan(vlan_id: int, name: str, subnet: str, description: str = "") -> None:
    """Add a new VLAN to the database and print the IOS commands."""
    if vlan_id in VLAN_DB:
        print(f"{RED}Error: VLAN {vlan_id} already exists.{RESET}")
        return

    # Validate subnet
    try:
        network = ipaddress.IPv4Network(subnet, strict=False)
        gateway = str(list(network.hosts())[0])
    except ValueError as e:
        print(f"{RED}Error: Invalid subnet '{subnet}'. {e}{RESET}")
        return

    VLAN_DB[vlan_id] = {
        "name": name.upper(),
        "subnet": str(network),
        "gateway": gateway,
        "description": description or f"{name} department",
        "color": "\033[36m",
    }

    print_header(f"VLAN {vlan_id} Added Successfully")
    print(f"  VLAN ID  : {vlan_id}")
    print(f"  Name     : {name.upper()}")
    print(f"  Subnet   : {network}")
    print(f"  Gateway  : {gateway}")
    print()
    print(f"{BOLD}Generated IOS Commands:{RESET}")
    print("─" * 40)
    print(f"! Create VLAN on switches")
    print(f"vlan {vlan_id}")
    print(f" name {name.upper()}")
    print(f"!")
    print(f"! Create SVI on Core-SW (Layer 3 switch)")
    print(f"interface vlan {vlan_id}")
    print(f" description Gateway-for-{name.upper()}")
    print(f" ip address {gateway} {network.netmask}")
    print(f" no shutdown")
    print(f"!")
    print(f"! Add VLAN to trunk links")
    print(f"interface GigabitEthernet0/1")
    print(f" switchport trunk allowed vlan add {vlan_id}")


def generate_port_config(vlan_id: int, device: str, ports: list) -> None:
    """Generate IOS access port configuration for given ports."""
    if vlan_id not in VLAN_DB:
        print(f"{RED}Error: VLAN {vlan_id} not found. Run --list to see valid VLANs.{RESET}")
        return

    vlan = VLAN_DB[vlan_id]
    print_header(f"Port Configuration: Device {device}, VLAN {vlan_id} ({vlan['name']})")
    print(f"! Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"! Device : {device}")
    print(f"! VLAN   : {vlan_id} ({vlan['name']})")
    print(f"! Subnet : {vlan['subnet']}")
    print()

    # Generate range command if ports are consecutive
    port_str = ",".join(ports) if len(ports) > 1 else ports[0]
    cmd_prefix = "interface range" if len(ports) > 1 else "interface"

    print(f"configure terminal")
    print(f"!")
    print(f"{cmd_prefix} {port_str}")
    print(f" description {vlan['name']}-Workstation")
    print(f" switchport mode access")
    print(f" switchport access vlan {vlan_id}")
    print(f" switchport nonegotiate")
    print(f" spanning-tree portfast")
    print(f" spanning-tree bpduguard enable")
    print(f" switchport port-security")
    print(f" switchport port-security maximum 1")
    print(f" switchport port-security mac-address sticky")
    print(f" switchport port-security violation shutdown")
    print(f" no shutdown")
    print(f"!")
    print(f"end")
    print(f"write memory")


def verify_connectivity(src_vlan: int, dst_vlan: int) -> None:
    """Simulate connectivity check between two VLANs based on ACL policy."""
    if src_vlan not in VLAN_DB:
        print(f"{RED}Error: Source VLAN {src_vlan} not found.{RESET}")
        return
    if dst_vlan not in VLAN_DB:
        print(f"{RED}Error: Destination VLAN {dst_vlan} not found.{RESET}")
        return

    src = VLAN_DB[src_vlan]
    dst = VLAN_DB[dst_vlan]
    allowed = ACL_POLICY.get((src_vlan, dst_vlan), True)

    print_header(f"Connectivity Check: VLAN {src_vlan} → VLAN {dst_vlan}")
    print(f"  Source      : VLAN {src_vlan} ({src['name']}) – {src['subnet']}")
    print(f"  Destination : VLAN {dst_vlan} ({dst['name']}) – {dst['subnet']}")
    print()

    # Simulate 5 ping packets
    if allowed:
        print(f"  Pinging {dst['gateway']} from VLAN {src_vlan} ({src['name']}):")
        for i in range(1, 6):
            print(f"    Packet {i}: Reply from {dst['gateway']}  {GREEN}[SUCCESS]{RESET}")
        print(f"\n  {GREEN}{BOLD}✔  Connectivity OK  (5/5 packets received){RESET}")
        print(f"  Route: {src['gateway']} → Core-SW SVI → {dst['gateway']}")
    else:
        print(f"  Pinging {dst['gateway']} from VLAN {src_vlan} ({src['name']}):")
        for i in range(1, 6):
            print(f"    Packet {i}: {RED}Request timed out  [BLOCKED by ACL]{RESET}")
        print(f"\n  {RED}{BOLD}✘  Connectivity BLOCKED  (0/5 packets received){RESET}")
        print(f"  Reason : ACL policy denies {src['name']} → {dst['name']} traffic")
        print(f"  ACL    : deny ip {src['subnet']} {dst['subnet']}")


def show_topology() -> None:
    """Print an ASCII representation of the network topology."""
    print_header("Network Topology – VLAN Overview")
    topology = """
                         ┌──────────────┐
                         │   INTERNET   │
                         └──────┬───────┘
                                │
                         ┌──────┴───────┐
                         │   Router0    │  192.168.0.1
                         │  (ROAS/GW)   │  Sub-interfaces:
                         │              │  .10 → VLAN10
                         └──────┬───────┘  .20 → VLAN20
                                │  Trunk   .30 → VLAN30
                         ┌──────┴───────┐
                         │   Core-SW    │  192.168.0.2
                         │  (Layer 3)   │  SVIs: Vlan10/20/30/40
                         └──┬──────┬──┬─┘
                  Trunk      │      │  │   Trunk
                 ┌───────────┘      │  └─────────────┐
                 │               Trunk               │
         ┌───────┴──────┐  ┌──────┴───────┐  ┌───────┴──────┐
         │    SW-A      │  │    SW-B      │  │    SW-C      │
         │    Sales     │  │   Finance    │  │      IT      │
         │ 192.168.0.10 │  │ 192.168.0.11 │  │ 192.168.0.12 │
         └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
                │                 │                  │
         VLAN 10 (access)  VLAN 20 (access)  VLAN 30 (access)
         10.10.10.0/24     10.20.20.0/24     10.30.30.0/24
    """
    print(topology)
    print(f"\n  {'VLAN':<6} {'Name':<12} {'Subnet':<20} {'Policy'}")
    print("  " + "─" * 56)
    for vid, v in sorted(VLAN_DB.items()):
        if vid == 99:
            continue
        policy = "Full access" if vid == 30 else ("No FINANCE" if vid == 10 else "No SALES" if vid == 20 else "Mgmt only")
        print(f"  {vid:<6} {v['name']:<12} {v['subnet']:<20} {policy}")


def export_config() -> None:
    """Export VLAN database to JSON."""
    filename = f"vlan_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    export_data = {
        "exported_at": datetime.now().isoformat(),
        "vlans": {str(k): v for k, v in VLAN_DB.items()},
    }
    with open(filename, "w") as f:
        json.dump(export_data, f, indent=2)
    print(f"{GREEN}✔ VLAN database exported to: {filename}{RESET}")


# ──────────────────────────────────────────────────────────────────
# Argument Parser
# ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="VLAN Configuration Manager – Generates Cisco IOS commands",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python vlan_manager.py --list
  python vlan_manager.py --add --id 50 --name HR --subnet 10.50.50.0/24
  python vlan_manager.py --generate --id 10 --device SW-A --ports fa0/1,fa0/2
  python vlan_manager.py --verify --src 10 --dst 20
  python vlan_manager.py --topology
  python vlan_manager.py --export
        """
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list",     action="store_true", help="List all VLANs")
    group.add_argument("--add",      action="store_true", help="Add a new VLAN")
    group.add_argument("--generate", action="store_true", help="Generate port config for a VLAN")
    group.add_argument("--verify",   action="store_true", help="Simulate connectivity check")
    group.add_argument("--topology", action="store_true", help="Show network topology")
    group.add_argument("--export",   action="store_true", help="Export VLAN DB to JSON")

    # --add arguments
    parser.add_argument("--id",          type=int,   help="VLAN ID (1–4094)")
    parser.add_argument("--name",        type=str,   help="VLAN name")
    parser.add_argument("--subnet",      type=str,   help="Subnet (e.g., 10.50.50.0/24)")
    parser.add_argument("--description", type=str,   help="VLAN description", default="")

    # --generate arguments
    parser.add_argument("--device", type=str, help="Switch hostname")
    parser.add_argument("--ports",  type=str, help="Comma-separated ports (e.g., fa0/1,fa0/2)")

    # --verify arguments
    parser.add_argument("--src", type=int, help="Source VLAN ID")
    parser.add_argument("--dst", type=int, help="Destination VLAN ID")

    args = parser.parse_args()

    if args.list:
        list_vlans()

    elif args.add:
        if not all([args.id, args.name, args.subnet]):
            parser.error("--add requires --id, --name, and --subnet")
        add_vlan(args.id, args.name, args.subnet, args.description)

    elif args.generate:
        if not all([args.id, args.device, args.ports]):
            parser.error("--generate requires --id, --device, and --ports")
        ports = [p.strip() for p in args.ports.split(",")]
        generate_port_config(args.id, args.device, ports)

    elif args.verify:
        if not all([args.src, args.dst]):
            parser.error("--verify requires --src and --dst")
        verify_connectivity(args.src, args.dst)

    elif args.topology:
        show_topology()

    elif args.export:
        export_config()


if __name__ == "__main__":
    main()
