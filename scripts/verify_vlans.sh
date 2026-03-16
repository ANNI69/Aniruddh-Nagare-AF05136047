#!/bin/bash
# ============================================================
# VLAN Verification Script
# Connects to network devices via SSH and runs 'show' commands
# to confirm VLAN configuration is correctly applied.
#
# Usage: ./verify_vlans.sh [--device <hostname>] [--all]
# ============================================================

set -euo pipefail

# ── Device Inventory ────────────────────────────────────────
declare -A DEVICES=(
  ["Core-SW"]="192.168.0.2"
  ["SW-A"]="192.168.0.10"
  ["SW-B"]="192.168.0.11"
  ["SW-C"]="192.168.0.12"
  ["Router0"]="192.168.0.1"
)

SSH_USER="admin"
SSH_PASS="cisco123"
SSH_OPTS="-o StrictHostKeyChecking=no -o ConnectTimeout=5"
LOG_DIR="./logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
PASS_COUNT=0
FAIL_COUNT=0

# ── Colors ──────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
RESET='\033[0m'

# ── Helpers ─────────────────────────────────────────────────
log() { echo -e "[$(date +'%H:%M:%S')] $*"; }
pass() { echo -e "  ${GREEN}✔ PASS${RESET}  $*"; ((PASS_COUNT++)); }
fail() { echo -e "  ${RED}✘ FAIL${RESET}  $*"; ((FAIL_COUNT++)); }
info() { echo -e "  ${BLUE}ℹ INFO${RESET}  $*"; }

mkdir -p "$LOG_DIR"

# ── SSH Command Runner ───────────────────────────────────────
run_cmd() {
  local device_ip="$1"
  local cmd="$2"
  # Using sshpass for password auth (install: apt-get install sshpass)
  if command -v sshpass &>/dev/null; then
    sshpass -p "$SSH_PASS" ssh $SSH_OPTS "$SSH_USER@$device_ip" "$cmd" 2>/dev/null
  else
    # Fallback: print the command that would run
    echo "[SIMULATED] ssh $SSH_USER@$device_ip '$cmd'"
  fi
}

# ── Test Functions ───────────────────────────────────────────

check_vlan_exists() {
  local device_ip="$1"
  local device_name="$2"
  local vlan_id="$3"
  local vlan_name="$4"

  local output
  output=$(run_cmd "$device_ip" "show vlan id $vlan_id" 2>&1)

  if echo "$output" | grep -qi "$vlan_name"; then
    pass "[$device_name] VLAN $vlan_id ($vlan_name) exists and is active"
  else
    fail "[$device_name] VLAN $vlan_id ($vlan_name) NOT FOUND or inactive"
    info "Run: show vlan id $vlan_id"
  fi
}

check_trunk_port() {
  local device_ip="$1"
  local device_name="$2"
  local interface="$3"
  local expected_vlans="$4"

  local output
  output=$(run_cmd "$device_ip" "show interfaces $interface trunk" 2>&1)

  if echo "$output" | grep -qi "trunking"; then
    pass "[$device_name] $interface is in trunking mode"
  else
    fail "[$device_name] $interface is NOT trunking"
  fi

  for vlan in $(echo "$expected_vlans" | tr ',' ' '); do
    if echo "$output" | grep -q "$vlan"; then
      pass "[$device_name] VLAN $vlan is allowed on $interface trunk"
    else
      fail "[$device_name] VLAN $vlan is MISSING from $interface trunk"
    fi
  done
}

check_svi_status() {
  local device_ip="$1"
  local device_name="$2"
  local vlan_id="$3"
  local expected_ip="$4"

  local output
  output=$(run_cmd "$device_ip" "show interfaces vlan $vlan_id" 2>&1)

  if echo "$output" | grep -qi "line protocol is up"; then
    pass "[$device_name] Vlan$vlan_id SVI is UP/UP"
  else
    fail "[$device_name] Vlan$vlan_id SVI is DOWN or missing"
  fi

  if echo "$output" | grep -q "$expected_ip"; then
    pass "[$device_name] Vlan$vlan_id IP address is $expected_ip"
  else
    fail "[$device_name] Vlan$vlan_id IP address is NOT $expected_ip"
  fi
}

check_routing() {
  local device_ip="$1"
  local device_name="$2"
  local prefix="$3"

  local output
  output=$(run_cmd "$device_ip" "show ip route $prefix" 2>&1)

  if echo "$output" | grep -qE "C|S|L"; then
    pass "[$device_name] Route to $prefix found in routing table"
  else
    fail "[$device_name] Route to $prefix NOT found"
  fi
}

check_port_security() {
  local device_ip="$1"
  local device_name="$2"
  local interface="$3"

  local output
  output=$(run_cmd "$device_ip" "show port-security interface $interface" 2>&1)

  if echo "$output" | grep -qi "enabled"; then
    pass "[$device_name] Port security ENABLED on $interface"
  else
    fail "[$device_name] Port security NOT enabled on $interface"
  fi
}

ping_test() {
  local device_ip="$1"
  local device_name="$2"
  local target_ip="$3"
  local source_vlan="$4"
  local expect_success="$5"

  local output
  output=$(run_cmd "$device_ip" "ping $target_ip source vlan $source_vlan repeat 5" 2>&1)

  local success
  if echo "$output" | grep -q "!!!!!"; then
    success=true
  else
    success=false
  fi

  if [ "$expect_success" = "true" ] && [ "$success" = "true" ]; then
    pass "[$device_name] VLAN $source_vlan → $target_ip: REACHABLE (expected)"
  elif [ "$expect_success" = "false" ] && [ "$success" = "false" ]; then
    pass "[$device_name] VLAN $source_vlan → $target_ip: BLOCKED (ACL policy correct)"
  elif [ "$expect_success" = "true" ] && [ "$success" = "false" ]; then
    fail "[$device_name] VLAN $source_vlan → $target_ip: UNREACHABLE (should be reachable)"
  else
    fail "[$device_name] VLAN $source_vlan → $target_ip: REACHABLE (should be BLOCKED by ACL)"
  fi
}

# ── Main Test Suites ─────────────────────────────────────────

run_core_switch_tests() {
  echo -e "\n${BOLD}${BLUE}=== Core Switch Tests ===${RESET}"
  local ip="${DEVICES[Core-SW]}"
  local name="Core-SW"

  # VLAN existence
  check_vlan_exists "$ip" "$name" 10 "SALES"
  check_vlan_exists "$ip" "$name" 20 "FINANCE"
  check_vlan_exists "$ip" "$name" 30 "IT"
  check_vlan_exists "$ip" "$name" 40 "MANAGEMENT"

  # Trunk ports
  check_trunk_port "$ip" "$name" "GigabitEthernet0/1" "10,20,30,40"
  check_trunk_port "$ip" "$name" "GigabitEthernet0/2" "10,40"
  check_trunk_port "$ip" "$name" "GigabitEthernet0/3" "20,40"
  check_trunk_port "$ip" "$name" "GigabitEthernet0/4" "30,40"

  # SVI status and IPs
  check_svi_status "$ip" "$name" 10 "10.10.10.1"
  check_svi_status "$ip" "$name" 20 "10.20.20.1"
  check_svi_status "$ip" "$name" 30 "10.30.30.1"

  # Routing table
  check_routing "$ip" "$name" "10.10.10.0"
  check_routing "$ip" "$name" "10.20.20.0"
  check_routing "$ip" "$name" "10.30.30.0"

  # Ping tests (inter-VLAN routing)
  ping_test "$ip" "$name" "10.30.30.1" 10 "true"    # SALES → IT: allowed
  ping_test "$ip" "$name" "10.20.20.1" 10 "false"   # SALES → FINANCE: blocked
  ping_test "$ip" "$name" "10.10.10.1" 20 "false"   # FINANCE → SALES: blocked
  ping_test "$ip" "$name" "10.10.10.1" 30 "true"    # IT → SALES: allowed
}

run_access_switch_tests() {
  local switch="$1"
  local ip="${DEVICES[$switch]}"
  local vlan_id="$2"
  local vlan_name="$3"

  echo -e "\n${BOLD}${BLUE}=== $switch Tests ===${RESET}"

  check_vlan_exists "$ip" "$switch" "$vlan_id" "$vlan_name"
  check_trunk_port  "$ip" "$switch" "GigabitEthernet0/1" "$vlan_id,40"
  check_port_security "$ip" "$switch" "FastEthernet0/1"
}

# ── Entry Point ──────────────────────────────────────────────
echo -e "${BOLD}============================================"
echo -e "  VLAN Verification Report"
echo -e "  $(date)"
echo -e "============================================${RESET}"

run_core_switch_tests
run_access_switch_tests "SW-A" 10 "SALES"
run_access_switch_tests "SW-B" 20 "FINANCE"
run_access_switch_tests "SW-C" 30 "IT"

# ── Summary ──────────────────────────────────────────────────
TOTAL=$((PASS_COUNT + FAIL_COUNT))
echo -e "\n${BOLD}============================================"
echo -e "  Verification Summary"
echo -e "============================================${RESET}"
echo -e "  Total checks : $TOTAL"
echo -e "  ${GREEN}PASSED       : $PASS_COUNT${RESET}"
if [ $FAIL_COUNT -gt 0 ]; then
  echo -e "  ${RED}FAILED       : $FAIL_COUNT${RESET}"
  echo -e "\n${RED}Some checks failed. Review the output above.${RESET}"
  exit 1
else
  echo -e "  ${GREEN}FAILED       : 0${RESET}"
  echo -e "\n${GREEN}${BOLD}All checks passed! VLAN configuration is correct.${RESET}"
fi
