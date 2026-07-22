# Traffic Matching Lists

#### `GET /v1/sites/{siteId}/traffic-matching-lists`
List traffic matching lists.

**Filterable:** `id`, `name`

#### `GET /v1/sites/{siteId}/traffic-matching-lists/{trafficMatchingListId}`
Get a traffic matching list.

#### `POST /v1/sites/{siteId}/traffic-matching-lists`
Create a traffic matching list. Discriminated by `type`:

**Ports:**
```json
{
  "type": "PORTS",
  "name": "Web Ports",
  "items": [
    { "type": "PORT_NUMBER", "value": 443 },
    { "type": "PORT_NUMBER_RANGE", "start": 8080, "stop": 8090 }
  ]
}
```

**IPv4 addresses:**
```json
{
  "type": "IPV4_ADDRESSES",
  "name": "Trusted Servers",
  "items": [
    { "type": "IP_ADDRESS", "value": "192.168.1.5" },
    { "type": "SUBNET", "value": "10.0.0.0/8" },
    { "type": "IP_ADDRESS_RANGE", "start": "192.168.1.10", "stop": "192.168.1.20" }
  ]
}
```

**IPv6 addresses:**
```json
{
  "type": "IPV6_ADDRESSES",
  "name": "IPv6 Hosts",
  "items": [
    { "type": "IP_ADDRESS", "value": "2001:db8::1" },
    { "type": "SUBNET", "value": "2001:db8::/32" }
  ]
}
```

**Port range:** 1-65535

#### `PUT /v1/sites/{siteId}/traffic-matching-lists/{trafficMatchingListId}`
Update a traffic matching list (same body as create).

#### `DELETE /v1/sites/{siteId}/traffic-matching-lists/{trafficMatchingListId}`
Delete a traffic matching list.
