---
name: unifi
description: >
  UniFi Network management via the `unifi` CLI (or the matching unifi_* MCP tools). Use when
  working with UniFi controllers, network devices, clients, WiFi, VLANs, firewall zones/policies,
  ACL rules, DNS policies, VPNs, or hotspot vouchers. Read this before running any unifi command.
allowed-tools: Bash(unifi list:*), Bash(unifi get:*)
---

# UniFi Network Management

One tool, two faces, same names: CLI command `unifi list devices` == MCP tool `unifi_list_devices`.
Prefer the CLI when a shell is available. Everything below uses CLI syntax; for MCP, join the
command words with `_` and pass the same arguments as tool parameters.

- **Config**: one file written by `unifi init` (env vars with the same names override). `site_id` is optional — single-site controllers auto-resolve.
- **Output**: JSON. Exit code 1 when the result is an error.
- **Destructive commands** (`delete`, `remove`, `restart`, `power`, `unauthorize`, `bulk`, `mongo write`, `ssh exec`, `provision`) require `--yes`.
- **Read-only mode**: `UNIFI_READ_ONLY=true` blocks all writes server-side.

## Gotchas

- **Pagination**: list endpoints return 25 items by default (vouchers: 100). Use `--offset` / `--limit` (max 200; vouchers 1000). Responses include `totalCount` — loop until you have everything.
- **Filtering**: most list/bulk commands accept `--filter` with `property.function(args)` syntax: `name.eq('Guest')`, `expired.eq(true)`, `name.like('cam*')`, `and(a,b)`, `not(x)`. String values in single quotes (escape `'` as `''`).
- **WiFi/Network creation**: the API requires many more fields than the schema suggests — use the complete payloads below; extra fields pass through.
- **ACL rule ordering**: lower `index` = higher priority (first-match-wins).
- **`get app info`**: returns `applicationVersion` only.

## Discovery (run these first)

```
unifi get app info                  → controller version
unifi list sites                    → site IDs
unifi list devices                  → adopted devices (name, model, mac, state)
unifi list pending-devices          → devices awaiting adoption
unifi list clients                  → connected clients (name, mac, ip, type)
unifi list networks                 → networks/VLANs
unifi list wifi                     → SSIDs
unifi list firewall-zones           → zone IDs (needed for network creation)
unifi list firewall-policies        → zone-based firewall policies
unifi list acl-rules                → ACL rules
unifi list dns-policies             → DNS policies
unifi list traffic-matching-lists   → port/IP lists for ACLs
unifi list wans / vpn-tunnels / vpn-servers / radius-profiles / device-tags / vouchers
unifi list switch-stacks / mc-lag-domains / lags
unifi list dpi-categories / dpi-applications / countries     (global; paginated)
```

## Devices

```bash
unifi get device <device-id>             # full detail: ports, uplink, firmware
unifi get device-stats <device-id>       # live: uptimeSec, cpuUtilizationPct, memoryUtilizationPct
unifi adopt device <mac>                 # adopt a pending device
unifi restart device <device-id> --yes
unifi remove device <device-id> --yes    # forget a device
unifi power cycle-port <switch-id> --port-idx 3 --yes
```

## Clients

```bash
unifi get client <client-id>             # type (WIRED/WIRELESS), ip, mac, uplinkDeviceId
unifi authorize guest <client-id>        # after captive portal
unifi unauthorize guest <client-id> --yes
```

## Create a GATEWAY Network

**Step 1:** get the zone ID from `unifi list firewall-zones` (Internal zone for standard networks).

**Step 2:** create with ALL required fields:

```bash
unifi create network --config '{
  "name": "IoT", "management": "GATEWAY", "vlanId": 40, "enabled": true,
  "isolationEnabled": false, "cellularBackupEnabled": false,
  "zoneId": "<firewall-zone-id>",
  "internetAccessEnabled": true, "mdnsForwardingEnabled": false,
  "ipv4Configuration": {
    "autoScaleEnabled": false,
    "hostIpAddress": "192.168.40.1", "prefixLength": 24,
    "dhcpConfiguration": {
      "mode": "SERVER",
      "ipAddressRange": {"start": "192.168.40.2", "stop": "192.168.40.254"},
      "leaseTimeSeconds": 259200,
      "pingConflictDetectionEnabled": true
    }
  }
}'
```

```bash
unifi get network <network-id>                # full detail with ipv4, DHCP, zoneId
unifi get network-references <network-id>     # what references this network — check before deleting
unifi update network <network-id> --config '{...}'   # PUT semantics — send the full config
unifi delete network <network-id> --yes
```

## Create a WiFi Broadcast

ALL these fields are required — omitting any causes HTTP 400:

```bash
unifi create wifi --config '{
  "name": "IoT WiFi", "type": "STANDARD", "enabled": true,
  "hideName": false,
  "broadcastingFrequenciesGHz": [2.4, 5, 6],
  "network": {"type": "SPECIFIC", "networkId": "<network-uuid>"},
  "securityConfiguration": {
    "type": "WPA2_WPA3_PERSONAL",
    "passphrase": "mypassword123",
    "pmfMode": "OPTIONAL",
    "fastRoamingEnabled": false,
    "saeConfiguration": {"anticloggingThresholdSeconds": 5, "syncTimeSeconds": 5},
    "wpa3FastRoamingEnabled": false
  },
  "clientIsolationEnabled": false,
  "multicastToUnicastConversionEnabled": true,
  "uapsdEnabled": true,
  "arpProxyEnabled": true,
  "bssTransitionEnabled": true
}'
```

`securityConfiguration.type`: `WPA2_PERSONAL` | `WPA3_PERSONAL` | `WPA2_WPA3_PERSONAL` | `OPEN`.
Optional: limit to specific APs with `"broadcastingDeviceFilter": {"type": "DEVICE_TAGS", "deviceTagIds": ["<tag-uuid>"]}` or `{"type": "DEVICES", "deviceIds": ["<device-uuid>"]}`.

## Firewall Zones & Policies

```bash
unifi create firewall-zone --config '{"name": "IoT Zone", "networkIds": ["<network-uuid>"]}'
unifi update firewall-zone <zone-id> --config '{"name": "IoT Zone", "networkIds": ["<id1>", "<id2>"]}'
unifi delete firewall-zone <zone-id> --yes      # system zones (Gateway, Internal, External, Hotspot, VPN, DMZ) cannot be deleted
```

Zone-based firewall policies (the modern firewall — preferred over ACLs on current firmware):

```bash
unifi list firewall-policies
unifi get firewall-policy <policy-id>            # copy an existing policy for the full payload shape
unifi create firewall-policy --config '{...}'    # name, action ALLOW|BLOCK|REJECT, source/destination {zoneId,...}, enabled
unifi get firewall-policy-ordering --source-zone-id <src> --destination-zone-id <dst>
unifi set firewall-policy-ordering --source-zone-id <src> --destination-zone-id <dst> --policy-ids id1,id2,id3
```

## ACL Rules

**IPv4 — block between networks:**
```bash
unifi create acl-rule --config '{
  "name": "Block IoT to LAN", "type": "IPV4", "action": "BLOCK",
  "enabled": true, "index": 0,
  "sourceFilter": {"type": "NETWORKS", "networkIds": ["<iot-network-uuid>"]},
  "destinationFilter": {"type": "NETWORKS", "networkIds": ["<lan-network-uuid>"]},
  "protocolFilter": ["TCP", "UDP"]
}'
```

**IPv4 — allow to specific IPs/ports:** `"destinationFilter": {"type": "IP_ADDRESSES_OR_SUBNETS", "ipAddressesOrSubnets": ["1.1.1.1", "8.8.8.8"], "portFilter": [53]}`

**MAC — block a device:**
```bash
unifi create acl-rule --config '{
  "name": "Block Device", "type": "MAC", "action": "BLOCK",
  "enabled": true, "index": 1,
  "networkIdFilter": "<network-uuid>",
  "sourceFilter": {"type": "MAC_ADDRESSES", "macAddresses": ["aa:bb:cc:dd:ee:ff"]}
}'
```

```bash
unifi get acl-ordering                       # evaluation order
unifi set acl-ordering --rule-ids id1,id2,id3
```

## Traffic Matching Lists

```bash
unifi create traffic-matching-list --config '{
  "type": "PORTS", "name": "Web Ports",
  "items": [{"type": "PORT_NUMBER", "value": 443}, {"type": "PORT_NUMBER_RANGE", "start": 8080, "stop": 8090}]
}'
unifi create traffic-matching-list --config '{
  "type": "IPV4_ADDRESSES", "name": "Trusted Servers",
  "items": [{"type": "IP_ADDRESS", "value": "192.168.1.5"}, {"type": "SUBNET", "value": "10.0.0.0/8"},
            {"type": "IP_ADDRESS_RANGE", "start": "192.168.1.10", "stop": "192.168.1.20"}]
}'
```

## Hotspot Vouchers

```bash
unifi create vouchers --config '{
  "name": "Event Pass", "timeLimitMinutes": 1440, "count": 10,
  "authorizedGuestLimit": 1, "dataUsageLimitMBytes": 1024,
  "rxRateLimitKbps": 10000, "txRateLimitKbps": 10000
}'
unifi bulk delete-vouchers --voucher-filter "expired.eq(true)" --yes
unifi bulk delete-vouchers --voucher-filter "name.eq('Event Pass')" --yes   # single quotes around values with spaces
```

## SSH Escape Hatch (settings the API doesn't expose)

Enabled by `UNIFI_SSH_KEY` (private key path) or `UNIFI_SSH_PASSWORD`; host defaults to the
controller from `UNIFI_HOST`, user to root. Use for radio config (channel/width/TX power/min-RSSI),
per-port profiles, controller settings, logs, tcpdump. **Never for anything the API covers** —
MongoDB writes are unvalidated, unsupported by Ubiquiti, and schemas drift across firmware.

Canonical workflow — API resolve → mongo write → provision → API verify:

```bash
unifi list devices --filter "model.eq('U7P')"        # 1. resolve MACs via the API
unifi mongo read "db.device.find({model:'U7P'}, {mac:1, radio_table:1}).toArray()"   # 2. inspect
unifi mongo write "db.device.updateMany({model:'U7P'}, {\$set: {'radio_table.\$[r].ht': '160'}}, {arrayFilters: [{'r.radio': 'na'}]})" --yes
unifi provision aa:bb:cc:dd:ee:01 aa:bb:cc:dd:ee:02 --yes   # 3. force-provision — DB writes are inert without this
unifi get device <device-id>                          # 4. verify
unifi ssh exec "tail -50 /mnt/data/unifi-os/unifi/logs/server.log" --yes   # raw shell for logs/tcpdump/diagnostics
```

Useful collections in the `ace` DB: `device` (radio_table, port_overrides), `setting`, `wlanconf`, `networkconf`, `portconf`.

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

387 articles across 11 sections. Read the per-section file for title/URL listings, or WebFetch any article URL.

| Section | Articles | File |
|---------|----------|------|
| Getting Started with UniFi | 20 | [help-getting-started-unifi.md](references/help-getting-started-unifi.md) |
| Features & Configuration | 138 | [help-features-config.md](references/help-features-config.md) |
| References & Specifications | 39 | [help-references-specs.md](references/help-references-specs.md) |
| Self-Hosted Network Server | 8 | [help-self-hosted.md](references/help-self-hosted.md) |
| Fabrics, Identity & RBAC | 6 | [help-fabrics-identity-rbac.md](references/help-fabrics-identity-rbac.md) |
| UniFi Endpoint | 6 | [help-unifi-endpoint.md](references/help-unifi-endpoint.md) |
| Advanced | 15 | [help-advanced.md](references/help-advanced.md) |
| VPN Configurations | 11 | [help-vpn.md](references/help-vpn.md) |
| Getting Started (Access, Talk, Connect) | 31 | [help-getting-started-access-talk-connect.md](references/help-getting-started-access-talk-connect.md) |
| UID Enterprise | 103 | [help-uid-enterprise.md](references/help-uid-enterprise.md) |
| Additional Resources | 10 | [help-additional-resources.md](references/help-additional-resources.md) |
