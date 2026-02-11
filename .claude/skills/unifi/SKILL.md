---
name: unifi
description: >
  IMMEDIATELY invoke this skill before using unifi-MCP tools. This skill provides guidance and examples for managing UniFi Network infrastructure via MCP tools. Use when working with UniFi controllers, network devices, clients, WiFi, VLANs, firewall zones, ACL rules, VPNs, or hotspot vouchers.
---

# UniFi Network Management

51 `mcp__unifi__unifi_*` tools. `site_id` is optional (auto-resolved for single-site controllers).

## Gotchas

- **Pagination**: All list endpoints return max 25 items (vouchers: 100). No offset/limit params exposed — you only get page 1.
- **WiFi/Network creation**: The API requires many more fields than the tool schema shows. All Pydantic models have `extra="allow"` so extra fields pass through — use the full payloads below.
- **Bulk delete filter syntax**: Values with spaces need single quotes: `name.eq('My Thing')`. Double quotes and unquoted both fail.
- **ACL rule ordering**: Lower `index` = higher priority (first-match-wins).
- **`get_app_info`**: Only returns `applicationVersion` — no hostname.

---

## Discovery (run these first)

```
unifi_get_app_info()                  → firmware version
unifi_list_sites()                    → site IDs
unifi_list_devices()                  → adopted devices (name, model, mac, state)
unifi_list_pending_devices()          → devices awaiting adoption
unifi_list_clients()                  → connected clients (name, mac, ip, type)
unifi_list_networks()                 → networks/VLANs
unifi_list_wifi()                     → SSIDs
unifi_list_firewall_zones()           → zone IDs (needed for network creation)
unifi_list_acl_rules()                → ACL rules
unifi_list_traffic_matching_lists()   → port/IP lists for ACLs
unifi_list_wans()                     → WAN interfaces
unifi_list_vpn_tunnels()              → site-to-site VPNs
unifi_list_vpn_servers()              → VPN servers
unifi_list_radius_profiles()          → RADIUS profiles
unifi_list_device_tags()              → device tags (used for WiFi broadcasting filters)
unifi_list_vouchers()                 → hotspot vouchers
unifi_list_dpi_categories()           → DPI categories (35 total, paginated)
unifi_list_dpi_applications()         → DPI apps (2112 total, paginated)
unifi_list_countries()                → countries for regulatory config (248 total, paginated)
```

## Devices

```python
unifi_get_device(device_id="<uuid>")        # full detail: ports, uplink, firmware, interfaces
unifi_get_device_stats(device_id="<uuid>")  # live: uptimeSec, cpuUtilizationPct, memoryUtilizationPct, load averages, uplink rates
unifi_restart_device(device_id="<uuid>")    # reboot
unifi_power_cycle_port(device_id="<switch-uuid>", port_idx=3)  # PoE cycle a port
```

## Clients

```python
unifi_get_client(client_id="<uuid>")         # detail: type (WIRED/WIRELESS), ip, mac, uplinkDeviceId
unifi_authorize_guest(client_id="<uuid>")    # authorize after captive portal
unifi_unauthorize_guest(client_id="<uuid>")  # revoke guest access
```

## Create a GATEWAY Network

**Step 1:** Get zone ID from `unifi_list_firewall_zones()` (Internal zone for standard networks).

**Step 2:** Create with ALL required fields:

```python
unifi_create_network(config={
    "name": "IoT", "management": "GATEWAY", "vlanId": 40, "enabled": True,
    "isolationEnabled": False, "cellularBackupEnabled": False,
    "zoneId": "<firewall-zone-id>",
    "internetAccessEnabled": True, "mdnsForwardingEnabled": False,
    "ipv4Configuration": {
        "autoScaleEnabled": False,
        "hostIpAddress": "192.168.40.1", "prefixLength": 24,
        "dhcpConfiguration": {
            "mode": "SERVER",
            "ipAddressRange": {"start": "192.168.40.2", "stop": "192.168.40.254"},
            "leaseTimeSeconds": 259200,
            "pingConflictDetectionEnabled": True
        }
    }
})
```

```python
unifi_get_network(network_id="<uuid>")                # full detail with ipv4, DHCP, zoneId
unifi_get_network_references(network_id="<uuid>")     # what WiFi/devices reference this network — check before deleting
unifi_update_network(network_id="<uuid>", config={...})  # PUT semantics — send full config
unifi_delete_network(network_id="<uuid>")              # check references first
```

## Create a WiFi Broadcast

ALL these fields are required — omitting any causes HTTP 400:

```python
unifi_create_wifi(config={
    "name": "IoT WiFi", "type": "STANDARD", "enabled": True,
    "hideName": False,  # True for hidden SSID
    "broadcastingFrequenciesGHz": [2.4, 5, 6],
    "network": {"type": "SPECIFIC", "networkId": "<network-uuid>"},
    "securityConfiguration": {
        "type": "WPA2_WPA3_PERSONAL",  # or WPA2_PERSONAL, WPA3_PERSONAL, OPEN
        "passphrase": "mypassword123",
        "pmfMode": "OPTIONAL",  # OPTIONAL or REQUIRED
        "fastRoamingEnabled": False,
        "saeConfiguration": {"anticloggingThresholdSeconds": 5, "syncTimeSeconds": 5},
        "wpa3FastRoamingEnabled": False
    },
    "clientIsolationEnabled": False,
    "multicastToUnicastConversionEnabled": True,
    "uapsdEnabled": True,
    "arpProxyEnabled": True,
    "bssTransitionEnabled": True
})
```

**Optional fields:** `broadcastingDeviceFilter` to limit to specific APs:
```python
"broadcastingDeviceFilter": {"type": "DEVICE_TAGS", "deviceTagIds": ["<tag-uuid>"]}
# or: {"type": "DEVICES", "deviceIds": ["<device-uuid>"]}
```

```python
unifi_get_wifi(wifi_id="<uuid>")                        # full detail including passphrase
unifi_update_wifi(wifi_id="<uuid>", config={...})       # PUT semantics — send full config
unifi_delete_wifi(wifi_id="<uuid>")
```

## Firewall Zones

```python
unifi_create_firewall_zone(config={"name": "IoT Zone", "networkIds": ["<network-uuid>"]})
unifi_get_firewall_zone(zone_id="<uuid>")
unifi_update_firewall_zone(zone_id="<uuid>", config={"name": "IoT Zone", "networkIds": ["<uuid1>", "<uuid2>"]})
unifi_delete_firewall_zone(zone_id="<uuid>")
```

System zones (Gateway, Internal, External, Hotspot, VPN, DMZ) cannot be deleted.

## ACL Rules

**IPv4 rule — block between networks:**
```python
unifi_create_acl_rule(config={
    "name": "Block IoT to LAN", "type": "IPV4", "action": "BLOCK",
    "enabled": True, "index": 0,
    "sourceFilter": {"type": "NETWORKS", "networkIds": ["<iot-network-uuid>"]},
    "destinationFilter": {"type": "NETWORKS", "networkIds": ["<lan-network-uuid>"]},
    "protocolFilter": ["TCP", "UDP"]  # or null for all protocols
})
```

**IPv4 rule — allow to specific IPs/ports:**
```python
unifi_create_acl_rule(config={
    "name": "Allow to DNS", "type": "IPV4", "action": "ALLOW",
    "enabled": True, "index": 0,
    "sourceFilter": {"type": "NETWORKS", "networkIds": ["<network-uuid>"]},
    "destinationFilter": {
        "type": "IP_ADDRESSES_OR_SUBNETS",
        "ipAddressesOrSubnets": ["1.1.1.1", "8.8.8.8"],
        "portFilter": [53]
    },
    "protocolFilter": ["TCP", "UDP"]
})
```

**MAC rule — block a device:**
```python
unifi_create_acl_rule(config={
    "name": "Block Device", "type": "MAC", "action": "BLOCK",
    "enabled": True, "index": 1,
    "networkIdFilter": "<network-uuid>",
    "sourceFilter": {"type": "MAC_ADDRESSES", "macAddresses": ["aa:bb:cc:dd:ee:ff"]}
})
```

```python
unifi_get_acl_rule(rule_id="<uuid>")
unifi_update_acl_rule(rule_id="<uuid>", config={...})  # PUT semantics — send full config
unifi_delete_acl_rule(rule_id="<uuid>")
```

## Traffic Matching Lists

**Ports:**
```python
unifi_create_traffic_matching_list(config={
    "type": "PORTS", "name": "Web Ports",
    "items": [
        {"type": "PORT_NUMBER", "value": 443},
        {"type": "PORT_NUMBER_RANGE", "start": 8080, "stop": 8090}
    ]
})
```

**IPv4 addresses:**
```python
unifi_create_traffic_matching_list(config={
    "type": "IPV4_ADDRESSES", "name": "Trusted Servers",
    "items": [
        {"type": "IP_ADDRESS", "value": "192.168.1.5"},
        {"type": "SUBNET", "value": "10.0.0.0/8"},
        {"type": "IP_ADDRESS_RANGE", "start": "192.168.1.10", "stop": "192.168.1.20"}
    ]
})
```

```python
unifi_get_traffic_matching_list(list_id="<uuid>")
unifi_update_traffic_matching_list(list_id="<uuid>", config={...})  # PUT semantics
unifi_delete_traffic_matching_list(list_id="<uuid>")
```

## Hotspot Vouchers

```python
# Create 10 vouchers, 24hr, with speed limits
unifi_create_vouchers(config={
    "name": "Event Pass", "timeLimitMinutes": 1440, "count": 10,
    "authorizedGuestLimit": 1,
    "dataUsageLimitMBytes": 1024,
    "rxRateLimitKbps": 10000,   # download limit
    "txRateLimitKbps": 10000    # upload limit
})

unifi_get_voucher(voucher_id="<uuid>")
unifi_delete_voucher(voucher_id="<uuid>")

# Bulk delete — filter requires single quotes for values with spaces
unifi_bulk_delete_vouchers(voucher_filter="expired.eq(true)")
unifi_bulk_delete_vouchers(voucher_filter="name.eq('Event Pass')")
```

## Auth

- `X-API-KEY` header (not Bearer token)
- Base path: `{host}/proxy/network/integration/v1/...`

## Domain References

| Domain | Docs | OpenAPI Schema |
|--------|------|----------------|
| Overview (auth, pagination, filtering) | [api-overview.md](references/api-overview.md) | -- |
| Devices | [devices.md](references/devices.md) | [schema-devices.json](references/schema-devices.json) |
| Clients | [clients.md](references/clients.md) | [schema-clients.json](references/schema-clients.json) |
| Networks | [networks.md](references/networks.md) | [schema-networks.json](references/schema-networks.json) |
| WiFi | [wifi.md](references/wifi.md) | [schema-wifi.json](references/schema-wifi.json) |
| Firewall & ACLs | [firewall.md](references/firewall.md) | [schema-firewall.json](references/schema-firewall.json) |
| Vouchers | [vouchers.md](references/vouchers.md) | [schema-vouchers.json](references/schema-vouchers.json) |
| Traffic Lists | [traffic-lists.md](references/traffic-lists.md) | [schema-traffic-lists.json](references/schema-traffic-lists.json) |
| WANs, VPNs, RADIUS, DPI, Tags | [supporting.md](references/supporting.md) | -- |

## UniFi Help Articles (help.ui.com)

387 articles from help.ui.com across 11 sections. Read the per-section file for full title/URL listings, or use `WebFetch` on any article URL for detailed guidance.

| Section | Articles | File | Covers |
|---------|----------|------|--------|
| Getting Started with UniFi | 20 | [help-getting-started-unifi.md](references/help-getting-started-unifi.md) | Setup, adoption, cloud architecture, API, roles, MFA, factory reset |
| Features & Configuration | 138 | [help-features-config.md](references/help-features-config.md) | WiFi, VLANs, firewall, NAT, IDS/IPS, QoS, Protect, Talk, Connect, Access, Drive, switches, HA |
| References & Specifications | 39 | [help-references-specs.md](references/help-references-specs.md) | PoE, SFP, DFS, LED indicators, antenna patterns, troubleshooting, Protect setup, CyberSecure |
| Self-Hosted Network Server | 8 | [help-self-hosted.md](references/help-self-hosted.md) | Linux/Windows install, updates, DB repair, tuning, system.properties |
| Fabrics, Identity & RBAC | 6 | [help-fabrics-identity-rbac.md](references/help-fabrics-identity-rbac.md) | Fabrics setup, IdP binding, Entra/AD/LDAP/Google integration, roles |
| UniFi Endpoint | 6 | [help-unifi-endpoint.md](references/help-unifi-endpoint.md) | ZTNA, endpoint agent, One-Click WiFi/VPN troubleshooting, MTU config |
| Advanced | 15 | [help-advanced.md](references/help-advanced.md) | SSH keys, L3 routing, 802.1x, RSSI, DHCP, ZTP, LAG, broadcast mgmt |
| VPN Configurations | 11 | [help-vpn.md](references/help-vpn.md) | WireGuard, OpenVPN, IPsec, L2TP, Teleport, Site Magic SD-WAN |
| Getting Started (Access, Talk, Connect) | 31 | [help-getting-started-access-talk-connect.md](references/help-getting-started-access-talk-connect.md) | Access hubs/readers/locks/wiring, Talk setup/calls, gate/elevator config |
| UID Enterprise | 103 | [help-uid-enterprise.md](references/help-uid-enterprise.md) | Admin guide, SSO apps, AD/LDAP, MDM, policies, MFA, VPN, legacy UI |
| Additional Resources | 10 | [help-additional-resources.md](references/help-additional-resources.md) | Early access, SIEM, hotspot API, NDAA compliance, E-Rate, ESD |
