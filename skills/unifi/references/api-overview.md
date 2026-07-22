# UniFi Network API Overview

**Version:** 10.0.162 | **Base URL:** `https://<controller-ip>/integration`

## Authentication

All requests require an API Key. Generate one in your UniFi application under **Settings > Integrations**.

```
GET /integration/v1/sites HTTP/1.1
X-API-KEY: <your-api-key>
```

## Request Format

- Content-Type: `application/json`
- All IDs are UUIDs
- Most endpoints are scoped to a site: `/v1/sites/{siteId}/...`

## Pagination

List endpoints support pagination via query parameters:

| Param | Default | Max | Description |
|-------|---------|-----|-------------|
| `offset` | 0 | - | Number of items to skip |
| `limit` | 25 | 200 | Items per page (vouchers: default 100, max 1000) |

Response envelope:
```json
{ "offset": 0, "limit": 25, "count": 10, "totalCount": 42, "data": [...] }
```

## Filtering

Many list/delete endpoints accept a `filter` query parameter.

**Syntax:** `property.function(arguments)`

| Operator | Args | Description | Types |
|----------|------|-------------|-------|
| `eq` | 1 | equals | STRING, INTEGER, DECIMAL, TIMESTAMP, BOOLEAN, UUID |
| `ne` | 1 | not equals | STRING, INTEGER, DECIMAL, TIMESTAMP, BOOLEAN, UUID |
| `gt` / `ge` / `lt` / `le` | 1 | comparisons | STRING, INTEGER, DECIMAL, TIMESTAMP, UUID |
| `like` | 1 | pattern match (`.` = one char, `*` = any) | STRING |
| `in` / `notIn` | 1+ | set membership | STRING, INTEGER, DECIMAL, TIMESTAMP, UUID |
| `isNull` / `isNotNull` | 0 | null check | all |
| `isEmpty` | 0 | empty set | SET |
| `contains` | 1 | set contains | SET |
| `containsAny` / `containsAll` / `containsExactly` | 1+ | set operations | SET |

**Compound:** `and(expr1, expr2)`, `or(expr1, expr2)`, `not(expr)`

**Type syntax:** Strings in `'single quotes'` (escape `'` with `''`). Timestamps as ISO 8601. UUIDs as `8-4-4-4-12`.

**Examples:**
```
?filter=name.eq('Guest Network')
?filter=and(enabled.eq(true), vlanId.gt(100))
?filter=not(name.like('guest*'))
```

## Error Response

```json
{
  "statusCode": 400,
  "statusName": "UNAUTHORIZED",
  "code": "api.authentication.missing-credentials",
  "message": "Missing credentials",
  "timestamp": "2024-11-27T08:13:46.966Z",
  "requestPath": "/integration/v1/sites/123",
  "requestId": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

## Application Info

#### `GET /v1/info`
Returns application version and runtime metadata.

**Response:**
```json
{ "applicationVersion": "9.1.0" }
```

## Sites

#### `GET /v1/sites`
List local sites. Site ID is required for most other API calls.

**Filterable:** `id` (UUID), `internalReference` (STRING), `name` (STRING)

**Response item:**
```json
{ "id": "uuid", "name": "Default", "internalReference": "default" }
```

## Metadata

Resources include a `metadata` object with an `origin` field indicating who created the resource:
- **User-defined:** Created via API or UI. Can be modified/deleted.
- **System-defined:** Created by the system. Some are configurable (e.g., firewall zones can have networks attached), but cannot be deleted.
- **Orchestrated:** Managed by external orchestration. May not be modifiable.

## Common Patterns

1. **Get your site ID first:** Call `GET /v1/sites` to discover site IDs before making site-scoped requests.
2. **Polymorphic bodies:** Create/update endpoints use a discriminator field (`type`, `management`, `mode`) to determine the schema variant. Always include the discriminator.
3. **Pagination:** Always check `totalCount` and paginate if `count < totalCount`.
4. **VLAN range:** 2-4000 for network VLAN IDs.
5. **Prefix length:** 8-30 for IPv4, 64-127 for IPv6.
