# Clients

#### `GET /v1/sites/{siteId}/clients`
List connected clients (wired, wireless, VPN, Teleport).

**Filterable:** `id`, `type`, `macAddress`, `ipAddress`, `connectedAt`, `access.type` (STRING: `DEFAULT`, `GUEST`), `access.authorized` (BOOLEAN)

**Client types:** `WIRED`, `WIRELESS`, `VPN`, `TELEPORT`

#### `GET /v1/sites/{siteId}/clients/{clientId}`
Get client details including name, IP, MAC, connection type, access info.

#### `POST /v1/sites/{siteId}/clients/{clientId}/actions`
Execute a client action.

**Available actions:** `AUTHORIZE_GUEST_ACCESS`, `UNAUTHORIZE_GUEST_ACCESS`

Authorize a guest (optional rate/data/time limits):
```json
{
  "action": "AUTHORIZE_GUEST_ACCESS",
  "timeLimitMinutes": 1440,
  "dataUsageLimitMBytes": 1024,
  "rxRateLimitKbps": 10000,
  "txRateLimitKbps": 10000
}
```

Unauthorize a guest (disconnects immediately):
```json
{ "action": "UNAUTHORIZE_GUEST_ACCESS" }
```

**Authorization response** includes `grantedAuthorization` (and `revokedAuthorization` if previously authorized) with fields: `authorizedAt`, `authorizationMethod` (`VOUCHER`/`API`/`OTHER`), `expiresAt`, rate limits, and `usage` (`durationSec`, `rxBytes`, `txBytes`, `bytes`).
