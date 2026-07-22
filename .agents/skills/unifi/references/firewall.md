# Firewall Zones & ACL Rules

## Firewall Zones

#### `GET /v1/sites/{siteId}/firewall/zones`
List firewall zones.

**Filterable:** `id`, `name`, `metadata.origin`, `metadata.configurable`

#### `GET /v1/sites/{siteId}/firewall/zones/{firewallZoneId}`
Get a firewall zone.

#### `POST /v1/sites/{siteId}/firewall/zones`
Create a custom firewall zone.

```json
{ "name": "IoT Zone", "networkIds": ["<network-uuid>"] }
```

#### `PUT /v1/sites/{siteId}/firewall/zones/{firewallZoneId}`
Update a firewall zone (same body as create).

#### `DELETE /v1/sites/{siteId}/firewall/zones/{firewallZoneId}`
Delete a custom firewall zone.

**Response fields:** `id`, `name`, `networkIds`, `metadata` (includes `origin` indicating user-defined vs system)

## ACL Rules (Access Control)

#### `GET /v1/sites/{siteId}/acl-rules`
List ACL rules.

**Filterable:** `type`, `id`, `enabled`, `name`, `description`, `action`, `index`, `protocolsFilter` (SET), `networkId`, `enforcingDeviceFilter.deviceIds` (SET), `metadata.origin`, `sourceFilter.*`, `destinationFilter.*`

#### `GET /v1/sites/{siteId}/acl-rules/{aclRuleId}`
Get an ACL rule.

#### `POST /v1/sites/{siteId}/acl-rules`
Create an ACL rule. Discriminated by `type`:

**IPv4 ACL rule:**
```json
{
  "type": "IPV4",
  "enabled": true,
  "name": "Block IoT to LAN",
  "action": "BLOCK",
  "index": 0,
  "sourceFilter": {
    "type": "NETWORKS",
    "networkIds": ["<iot-network-uuid>"]
  },
  "destinationFilter": {
    "type": "IP_ADDRESSES_OR_SUBNETS",
    "ipAddressesOrSubnets": ["192.168.1.0/24"],
    "portFilter": [80, 443]
  },
  "protocolFilter": ["TCP", "UDP"]
}
```

**MAC ACL rule:**
```json
{
  "type": "MAC",
  "enabled": true,
  "name": "Block Device",
  "action": "BLOCK",
  "index": 1,
  "networkIdFilter": "<network-uuid>",
  "sourceFilter": {
    "type": "MAC_ADDRESSES",
    "macAddresses": ["aa:bb:cc:dd:ee:ff"]
  }
}
```

**Actions:** `ALLOW`, `BLOCK`
**Index:** Lower = higher priority (min: 0)
**Enforcing device filter:** `null` = all switches, or `{ "type": "DEVICES", "deviceIds": [...] }`
**IP endpoint types:** `IP_ADDRESSES_OR_SUBNETS` (with optional `portFilter`) or `NETWORKS` (with `networkIds`)
**MAC endpoint type:** `MAC_ADDRESSES` (with `macAddresses`, optional `prefixLength` 1-48)

#### `PUT /v1/sites/{siteId}/acl-rules/{aclRuleId}`
Update an ACL rule (same body as create).

#### `DELETE /v1/sites/{siteId}/acl-rules/{aclRuleId}`
Delete a user-defined ACL rule.
