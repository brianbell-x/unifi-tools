# WiFi Broadcasts

#### `GET /v1/sites/{siteId}/wifi/broadcasts`
List WiFi broadcasts (SSIDs).

**Filterable:** `type`, `id`, `enabled`, `name`, `broadcastingFrequenciesGHz` (SET), `metadata.origin`, `network.type`, `network.networkId`, `securityConfiguration.type`, `broadcastingDeviceFilter.type`, `broadcastingDeviceFilter.deviceIds` (SET), `broadcastingDeviceFilter.deviceTagIds` (SET), `hotspotConfiguration.type`

#### `GET /v1/sites/{siteId}/wifi/broadcasts/{wifiBroadcastId}`
Get WiFi broadcast details.

#### `POST /v1/sites/{siteId}/wifi/broadcasts`
Create a WiFi broadcast. Discriminated by `type`:

**STANDARD WiFi:**
```json
{
  "type": "STANDARD",
  "name": "My WiFi",
  "enabled": true,
  "broadcastingFrequenciesGHz": ["2.4", "5", "6"],
  "network": { "type": "SPECIFIC", "networkId": "<uuid>" },
  "securityConfiguration": {
    "type": "WPA2_PERSONAL",
    "passphrase": "mypassword123"
  },
  "hideName": false,
  "clientIsolationEnabled": false,
  "multicastToUnicastConversionEnabled": true,
  "uapsdEnabled": true,
  "arpProxyEnabled": true,
  "bssTransitionEnabled": true
}
```

**IOT_OPTIMIZED WiFi:** Same as STANDARD but without frequency/band/hotspot options.

**Security types:** `OPEN`, `WPA2_PERSONAL`, `WPA3_PERSONAL`, `WPA2_WPA3_PERSONAL`, `WPA2_ENTERPRISE`, `WPA3_ENTERPRISE`, `WPA2_WPA3_ENTERPRISE`

- Personal types require `passphrase` (8-63 chars)
- Enterprise types require `radiusConfiguration` with `profileId` and `nasId`
- WPA3 types require `saeConfiguration` (`anticloggingThresholdSeconds`, `syncTimeSeconds`)
- `pmfMode`: `REQUIRED` or `OPTIONAL`

**Network reference:** `NATIVE` (default network) or `SPECIFIC` (with `networkId`)

**Broadcasting device filter:** `null` (all APs), `DEVICES` (specific `deviceIds`), or `DEVICE_TAGS` (specific `deviceTagIds`)

**Hotspot config:** `CAPTIVE_PORTAL` or `PASSPOINT`

**Optional features:**
- `bandSteeringEnabled`, `mloEnabled` (multi-link operation)
- `blackoutScheduleConfiguration` with per-day schedules (`ALL_DAY` or `TIME_RANGE`)
- `clientFilteringPolicy` with `action` (`ALLOW`/`BLOCK`) and `macAddressFilter` (max 512)
- `multicastFilteringPolicy` with `action` (`ALLOW` with `sourceMacAddressFilter`, or `BLOCK`)
- `mdnsProxyConfiguration` mode `AUTO` or `CUSTOM` with policies
- `basicDataRateKbpsByFrequencyGHz` per-band minimum rates
- `dtimPeriodByFrequencyGHzOverride` per-band DTIM (1-255)

#### `PUT /v1/sites/{siteId}/wifi/broadcasts/{wifiBroadcastId}`
Update a WiFi broadcast (same body as create).

#### `DELETE /v1/sites/{siteId}/wifi/broadcasts/{wifiBroadcastId}`
Delete a WiFi broadcast. Query param `force` (boolean, default false).
