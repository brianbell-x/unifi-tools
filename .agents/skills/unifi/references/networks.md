# Networks

#### `GET /v1/sites/{siteId}/networks`
List all networks on a site.

**Filterable:** `management`, `id`, `name`, `enabled`, `vlanId`, `deviceId`, `metadata.origin`

#### `GET /v1/sites/{siteId}/networks/{networkId}`
Get network details.

#### `POST /v1/sites/{siteId}/networks`
Create a network. Discriminated by `management`:

**GATEWAY managed:**
```json
{
  "management": "GATEWAY",
  "name": "My Network",
  "enabled": true,
  "vlanId": 100,
  "isolationEnabled": false,
  "cellularBackupEnabled": false,
  "internetAccessEnabled": true,
  "mdnsForwardingEnabled": false,
  "zoneId": "<firewall-zone-uuid>",
  "ipv4Configuration": {
    "autoScaleEnabled": false,
    "hostIpAddress": "192.168.100.1",
    "prefixLength": 24,
    "dhcpConfiguration": {
      "mode": "SERVER",
      "ipAddressRange": { "start": "192.168.100.10", "stop": "192.168.100.254" },
      "leaseTimeSeconds": 86400,
      "pingConflictDetectionEnabled": true
    }
  }
}
```

**SWITCH managed:**
```json
{
  "management": "SWITCH",
  "name": "Switch Network",
  "enabled": true,
  "vlanId": 200,
  "isolationEnabled": false,
  "cellularBackupEnabled": false,
  "deviceId": "<l3-switch-uuid>",
  "ipv4Configuration": {
    "autoScaleEnabled": false,
    "hostIpAddress": "10.0.0.1",
    "prefixLength": 24
  }
}
```

**UNMANAGED:**
```json
{ "management": "UNMANAGED", "name": "External", "enabled": true, "vlanId": 300 }
```

#### `PUT /v1/sites/{siteId}/networks/{networkId}`
Update a network (same body as create).

#### `DELETE /v1/sites/{siteId}/networks/{networkId}`
Delete a network.

| Query Param | Type | Description |
|-------------|------|-------------|
| `cascade` | boolean | Delete dependent resources |
| `force` | boolean | Force deletion |

#### `GET /v1/sites/{siteId}/networks/{networkId}/references`
Get references to a specific network (what uses it).

**Resource types:** `CLIENT`, `DEVICE`, `STATIC_ROUTE`, `OSPF_ROUTE`, `NEXT_AI`, `WIFI`, `NAT_RULE`, `SD_WAN`

**Response:** `{ "referenceResources": [{ "resourceType": "WIFI", "referenceCount": 2, "references": [{ "referenceId": "<uuid>" }] }] }`

**DHCP modes:** `SERVER` (full DHCP with range, DNS, lease, PXE, NTP, WINS, WPAD, TFTP options) or `RELAY` (forward to `dhcpServerIpAddresses`).

**IPv6:** Optional. Set `interfaceType` to `STATIC` (with `hostIpAddress`, `prefixLength`) or `PREFIX_DELEGATION` (with `prefixDelegationWanInterfaceId`). Supports SLAAC and/or DHCPv6.

**NAT outbound:** `AUTO` (select `MAIN` or `ALL` IPs) or `STATIC` (explicit IP selectors).
