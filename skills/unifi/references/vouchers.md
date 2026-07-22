# Hotspot Vouchers

#### `GET /v1/sites/{siteId}/hotspot/vouchers`
List vouchers (default limit 100, max 1000).

**Filterable:** `id`, `createdAt`, `name`, `code`, `authorizedGuestLimit`, `authorizedGuestCount`, `activatedAt`, `expiresAt`, `expired`, `timeLimitMinutes`, `dataUsageLimitMBytes`, `rxRateLimitKbps`, `txRateLimitKbps`

#### `GET /v1/sites/{siteId}/hotspot/vouchers/{voucherId}`
Get voucher details.

#### `POST /v1/sites/{siteId}/hotspot/vouchers`
Generate one or more vouchers.

```json
{
  "name": "Event Pass",
  "count": 10,
  "timeLimitMinutes": 1440,
  "authorizedGuestLimit": 1,
  "dataUsageLimitMBytes": 1024,
  "rxRateLimitKbps": 10000,
  "txRateLimitKbps": 10000
}
```

| Field | Required | Range |
|-------|----------|-------|
| `name` | yes | - |
| `timeLimitMinutes` | yes | 1-1000000 |
| `count` | no | 1-1000 (default 1) |
| `authorizedGuestLimit` | no | min 1 |
| `dataUsageLimitMBytes` | no | 1-1048576 |
| `rxRateLimitKbps` / `txRateLimitKbps` | no | 2-100000 |

**Response:** `{ "vouchers": [...] }` array of created voucher details with `id`, `code`, `createdAt`, etc.

#### `DELETE /v1/sites/{siteId}/hotspot/vouchers/{voucherId}`
Delete a specific voucher. Returns `{ "vouchersDeleted": <count> }`.

#### `DELETE /v1/sites/{siteId}/hotspot/vouchers`
Bulk delete vouchers by filter (**filter is required**). Same filterable properties as list.
