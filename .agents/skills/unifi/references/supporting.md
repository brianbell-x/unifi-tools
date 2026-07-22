# Supporting Resources (Read-Only)

#### `GET /v1/sites/{siteId}/wans`
List WAN interfaces. Returns `id` and `name` for each interface.

#### `GET /v1/sites/{siteId}/vpn/site-to-site-tunnels`
List site-to-site VPN tunnels.

**Tunnel types:** `OPENVPN`, `IPSEC`, `WIREGUARD`

**Filterable:** `type`, `id`, `name`, `metadata.origin`, `metadata.source`

#### `GET /v1/sites/{siteId}/vpn/servers`
List VPN servers.

**Server types:** `OPENVPN`, `WIREGUARD`, `L2TP`, `PPTP`, `UID`

**Filterable:** `type`, `id`, `name`, `enabled`, `metadata.origin`

#### `GET /v1/sites/{siteId}/radius/profiles`
List RADIUS profiles.

**Filterable:** `id`, `name`, `metadata.origin`

#### `GET /v1/sites/{siteId}/device-tags`
List device tags (used for WiFi broadcast AP assignments).

**Filterable:** `id`, `name`, `deviceIds` (SET)

#### `GET /v1/dpi/categories`
List DPI categories (not site-scoped).

**Filterable:** `id` (INTEGER), `name`

#### `GET /v1/dpi/applications`
List DPI applications (not site-scoped).

**Filterable:** `id` (INTEGER), `name`

#### `GET /v1/countries`
List ISO country codes (not site-scoped).

**Filterable:** `code`, `name`
