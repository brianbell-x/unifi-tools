# UniFi Devices

#### `GET /v1/sites/{siteId}/devices`
List adopted devices with basic info.

**Filterable:** `id`, `macAddress`, `ipAddress`, `name`, `model`, `state`, `supported`, `firmwareVersion`, `firmwareUpdatable`, `features` (SET), `interfaces` (SET)

**Response item fields:** `id`, `macAddress`, `ipAddress`, `name`, `model`, `state`, `supported`, `firmwareVersion`, `firmwareUpdatable`, `features` (array: `switching`, `accessPoint`, `gateway`), `interfaces`

#### `GET /v1/sites/{siteId}/devices/{deviceId}`
Get full device details including firmware, uplink state, ports, radios.

#### `GET /v1/sites/{siteId}/devices/{deviceId}/statistics/latest`
Real-time device stats: uptime, throughput, CPU, memory.

#### `GET /v1/sites/{siteId}/devices/{deviceId}`
Get full device details including firmware, uplink, ports, radios.

**Response fields:** `id`, `macAddress`, `ipAddress`, `name`, `model`, `supported`, `state`, `firmwareVersion`, `firmwareUpdatable`, `adoptedAt`, `provisionedAt`, `configurationId`, `uplink` (`deviceId`), `features` (`switching`, `accessPoint`), `interfaces` (`ports`, `radios`)

**Port fields:** `idx`, `state` (`UP`/`DOWN`/`UNKNOWN`), `connector` (`RJ45`/`SFP`/`SFPPLUS`/`SFP28`/`QSFP28`), `maxSpeedMbps`, `speedMbps`, `poe` (with `standard`: `802.3af`/`802.3at`/`802.3bt`, `type`: 1-4, `enabled`, `state`: `UP`/`DOWN`/`LIMITED`/`UNKNOWN`)

**Radio fields:** `wlanStandard` (`802.11a`/`b`/`g`/`n`/`ac`/`ax`/`be`), `frequencyGHz` (`2.4`/`5`/`6`/`60`), `channelWidthMHz`, `channel`

#### `GET /v1/sites/{siteId}/devices/{deviceId}/statistics/latest`
Real-time device stats.

**Response fields:** `uptimeSec`, `lastHeartbeatAt`, `nextHeartbeatAt`, `loadAverage1Min`/`5Min`/`15Min`, `cpuUtilizationPct`, `memoryUtilizationPct`, `uplink` (`txRateBps`, `rxRateBps`), `interfaces.radios[]` (`frequencyGHz`, `txRetriesPct`)

#### `POST /v1/sites/{siteId}/devices/{deviceId}/actions`
Execute an action on an adopted device.

**Available action:** `RESTART`
```json
{ "action": "RESTART" }
```

#### `POST /v1/sites/{siteId}/devices/{deviceId}/interfaces/ports/{portIdx}/actions`
Execute an action on a specific device port.

**Available action:** `POWER_CYCLE` (PoE power cycle)
```json
{ "action": "POWER_CYCLE" }
```

#### `GET /v1/pending-devices`
List devices pending adoption (not scoped to a site).

**Filterable:** `macAddress`, `ipAddress`, `model`, `state`, `supported`, `firmwareVersion`, `firmwareUpdatable`, `features` (SET)

**Device states:** `ONLINE`, `OFFLINE`, `PENDING_ADOPTION`, `UPDATING`, `GETTING_READY`, `ADOPTING`, `DELETING`, `CONNECTION_INTERRUPTED`, `ISOLATED`, `U5G_INCORRECT_TOPOLOGY`
