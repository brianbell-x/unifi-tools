"""UniFi Network Integration API tools (official API, v10.3.58 coverage).

Auth: X-API-KEY header. Base: {UNIFI_HOST}/proxy/network/integration/v1.
List endpoints paginate via offset/limit (default 25, max 200; vouchers 100/1000) and return
{offset, limit, count, totalCount, data}. Filter syntax: property.function(args), e.g.
name.eq('Guest'), expired.eq(true), name.like('cam*'), and(a,b), not(x) — strings in single quotes.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .core import _api, _page, _site, tool

# ── Input Models (extra fields pass through to the API) ──


class NetworkConfig(BaseModel):
    """Network config. Shape varies by management type (GATEWAY, SWITCH, UNMANAGED). The API
    requires more fields than listed — see the unifi skill references for complete payloads."""
    model_config = ConfigDict(extra="allow")
    name: str
    management: str = Field(description="GATEWAY | SWITCH | UNMANAGED")
    enabled: bool = True
    vlanId: int | None = Field(None, ge=2, le=4000)
    ipv4Configuration: dict | None = None
    dhcpConfiguration: dict | None = None


class WifiConfig(BaseModel):
    """WiFi broadcast config. The API requires the full field set on create — see the unifi skill
    references for complete payloads (securityConfiguration, broadcastingFrequenciesGHz, etc.)."""
    model_config = ConfigDict(extra="allow")
    name: str
    type: str = Field("STANDARD", description="STANDARD | IOT_OPTIMIZED")
    enabled: bool = True
    band: str | None = None
    securityConfiguration: dict | None = None
    networkId: str | None = None


class AclRuleConfig(BaseModel):
    """ACL rule config. Lower index = higher priority (first-match-wins)."""
    model_config = ConfigDict(extra="allow")
    name: str
    type: str = Field(description="IPV4 | MAC")
    action: str = Field(description="ALLOW | BLOCK")
    enabled: bool = True
    index: int | None = None
    sourceFilter: dict | None = None
    destinationFilter: dict | None = None
    protocolFilter: list[str] | None = None


class TrafficMatchingListConfig(BaseModel):
    """Traffic matching list: name, type (PORTS|IPV4_ADDRESSES|IPV6_ADDRESSES), items (list of dicts)."""
    model_config = ConfigDict(extra="allow")
    name: str
    type: str = Field(description="PORTS | IPV4_ADDRESSES | IPV6_ADDRESSES")
    items: list[dict] = Field(default_factory=list)


class VoucherCreateInput(BaseModel):
    """Voucher creation: name, timeLimitMinutes, count, optional guest/data/rate limits."""
    model_config = ConfigDict(extra="allow")
    name: str
    timeLimitMinutes: int = Field(ge=1, le=1000000)
    count: int = Field(1, ge=1, le=1000)
    dataUsageLimitMBytes: int | None = None
    rxRateLimitKbps: int | None = None
    txRateLimitKbps: int | None = None


class FirewallZoneInput(BaseModel):
    """Firewall zone: name plus member network IDs."""
    model_config = ConfigDict(extra="allow")
    name: str
    networkIds: list[str] = Field(default_factory=list)


# ── Info & Sites ──


@tool(read_only=True)
async def unifi_get_app_info() -> Any:
    """Get UniFi Network application info ({applicationVersion})."""
    return await _api("GET", "/v1/info")


@tool(read_only=True)
async def unifi_list_sites(offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List all sites managed by this UniFi controller."""
    return await _api("GET", "/v1/sites", params=_page(offset, limit, filter))


# ── Devices ──


@tool(read_only=True)
async def unifi_list_devices(site_id: str | None = None, offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List adopted devices at a site (name, model, mac, state, firmware). Paginated; limit max 200."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/devices", params=_page(offset, limit, filter))


@tool(read_only=True)
async def unifi_get_device(device_id: str, site_id: str | None = None) -> Any:
    """Get detailed info for a single device (ports, uplink, firmware, interfaces)."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/devices/{device_id}")


@tool(read_only=True)
async def unifi_get_device_stats(device_id: str, site_id: str | None = None) -> Any:
    """Get latest device statistics (uptime, throughput, CPU, memory)."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/devices/{device_id}/statistics/latest")


@tool(destructive=True)
async def unifi_restart_device(device_id: str, site_id: str | None = None) -> Any:
    """Restart (reboot) a device."""
    return await _api("POST", f"/v1/sites/{await _site(site_id)}/devices/{device_id}/actions", body={"action": "RESTART"})


@tool(destructive=True)
async def unifi_power_cycle_port(device_id: str, port_idx: int, site_id: str | None = None) -> Any:
    """Power-cycle a specific PoE port on a switch."""
    return await _api("POST", f"/v1/sites/{await _site(site_id)}/devices/{device_id}/interfaces/ports/{port_idx}/actions", body={"action": "POWER_CYCLE"})


@tool(read_only=True)
async def unifi_list_pending_devices(offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List devices pending adoption (not yet site-scoped)."""
    return await _api("GET", "/v1/pending-devices", params=_page(offset, limit, filter))


@tool()
async def unifi_adopt_device(mac_address: str, site_id: str | None = None, ignore_device_limit: bool = False) -> Any:
    """Adopt a pending device by MAC address into a site."""
    return await _api("POST", f"/v1/sites/{await _site(site_id)}/devices", body={"macAddress": mac_address, "ignoreDeviceLimit": ignore_device_limit})


@tool(destructive=True)
async def unifi_remove_device(device_id: str, site_id: str | None = None) -> Any:
    """Remove (forget) an adopted device from a site."""
    return await _api("DELETE", f"/v1/sites/{await _site(site_id)}/devices/{device_id}")


# ── Clients ──


@tool(read_only=True)
async def unifi_list_clients(site_id: str | None = None, offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List connected clients at a site (name, mac, ip, type, network). Paginated; limit max 200."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/clients", params=_page(offset, limit, filter))


@tool(read_only=True)
async def unifi_get_client(client_id: str, site_id: str | None = None) -> Any:
    """Get detailed info for a single client."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/clients/{client_id}")


@tool()
async def unifi_authorize_guest(client_id: str, site_id: str | None = None) -> Any:
    """Authorize a guest client (e.g. after captive portal)."""
    return await _api("POST", f"/v1/sites/{await _site(site_id)}/clients/{client_id}/actions", body={"action": "AUTHORIZE_GUEST"})


@tool(destructive=True)
async def unifi_unauthorize_guest(client_id: str, site_id: str | None = None) -> Any:
    """Revoke guest authorization for a client."""
    return await _api("POST", f"/v1/sites/{await _site(site_id)}/clients/{client_id}/actions", body={"action": "UNAUTHORIZE_GUEST"})


# ── Networks ──


@tool(read_only=True)
async def unifi_list_networks(site_id: str | None = None, offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List networks at a site (name, management type, vlanId, subnet)."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/networks", params=_page(offset, limit, filter))


@tool(read_only=True)
async def unifi_get_network(network_id: str, site_id: str | None = None) -> Any:
    """Get detailed info for a single network."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/networks/{network_id}")


@tool()
async def unifi_create_network(config: NetworkConfig, site_id: str | None = None) -> Any:
    """Create a network. Requires the full payload (zoneId, ipv4Configuration, dhcpConfiguration...) — see skill references."""
    return await _api("POST", f"/v1/sites/{await _site(site_id)}/networks", body=config.model_dump(exclude_none=True))


@tool(idempotent=True)
async def unifi_update_network(network_id: str, config: NetworkConfig, site_id: str | None = None) -> Any:
    """Update a network. PUT semantics — send the full config."""
    return await _api("PUT", f"/v1/sites/{await _site(site_id)}/networks/{network_id}", body=config.model_dump(exclude_none=True))


@tool(destructive=True)
async def unifi_delete_network(network_id: str, site_id: str | None = None) -> Any:
    """Delete a network. Check unifi_get_network_references first."""
    return await _api("DELETE", f"/v1/sites/{await _site(site_id)}/networks/{network_id}")


@tool(read_only=True)
async def unifi_get_network_references(network_id: str, site_id: str | None = None) -> Any:
    """List resources referencing this network (WiFi, zones, etc.). Check before deleting."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/networks/{network_id}/references")


# ── WiFi Broadcasts ──


@tool(read_only=True)
async def unifi_list_wifi(site_id: str | None = None, offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List WiFi broadcasts (SSIDs) at a site."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/wifi/broadcasts", params=_page(offset, limit, filter))


@tool(read_only=True)
async def unifi_get_wifi(wifi_id: str, site_id: str | None = None) -> Any:
    """Get detailed info for a single WiFi broadcast (includes passphrase)."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/wifi/broadcasts/{wifi_id}")


@tool()
async def unifi_create_wifi(config: WifiConfig, site_id: str | None = None) -> Any:
    """Create a WiFi broadcast. Requires the full payload (securityConfiguration, broadcastingFrequenciesGHz...) — see skill references."""
    return await _api("POST", f"/v1/sites/{await _site(site_id)}/wifi/broadcasts", body=config.model_dump(exclude_none=True))


@tool(idempotent=True)
async def unifi_update_wifi(wifi_id: str, config: WifiConfig, site_id: str | None = None) -> Any:
    """Update a WiFi broadcast. PUT semantics — send the full config."""
    return await _api("PUT", f"/v1/sites/{await _site(site_id)}/wifi/broadcasts/{wifi_id}", body=config.model_dump(exclude_none=True))


@tool(destructive=True)
async def unifi_delete_wifi(wifi_id: str, site_id: str | None = None) -> Any:
    """Delete a WiFi broadcast."""
    return await _api("DELETE", f"/v1/sites/{await _site(site_id)}/wifi/broadcasts/{wifi_id}")


# ── Hotspot Vouchers ──


@tool(read_only=True)
async def unifi_list_vouchers(site_id: str | None = None, offset: int = 0, limit: int = 100, filter: str | None = None) -> Any:
    """List hotspot vouchers. Paginated; limit default 100, max 1000."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/hotspot/vouchers", params=_page(offset, limit, filter))


@tool(read_only=True)
async def unifi_get_voucher(voucher_id: str, site_id: str | None = None) -> Any:
    """Get detailed info for a single voucher."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/hotspot/vouchers/{voucher_id}")


@tool()
async def unifi_create_vouchers(config: VoucherCreateInput, site_id: str | None = None) -> Any:
    """Create hotspot vouchers (name, timeLimitMinutes, count, optional data/rate limits)."""
    return await _api("POST", f"/v1/sites/{await _site(site_id)}/hotspot/vouchers", body=config.model_dump(exclude_none=True))


@tool(destructive=True)
async def unifi_delete_voucher(voucher_id: str, site_id: str | None = None) -> Any:
    """Delete a single voucher."""
    return await _api("DELETE", f"/v1/sites/{await _site(site_id)}/hotspot/vouchers/{voucher_id}")


@tool(destructive=True)
async def unifi_bulk_delete_vouchers(voucher_filter: str, site_id: str | None = None) -> Any:
    """Bulk-delete vouchers matching a filter expression (required), e.g. expired.eq(true) or name.eq('Event Pass') — single quotes around values with spaces."""
    return await _api("DELETE", f"/v1/sites/{await _site(site_id)}/hotspot/vouchers", params={"filter": voucher_filter})


# ── Firewall Zones ──


@tool(read_only=True)
async def unifi_list_firewall_zones(site_id: str | None = None, offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List firewall zones at a site."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/firewall/zones", params=_page(offset, limit, filter))


@tool(read_only=True)
async def unifi_get_firewall_zone(zone_id: str, site_id: str | None = None) -> Any:
    """Get detailed info for a single firewall zone."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/firewall/zones/{zone_id}")


@tool()
async def unifi_create_firewall_zone(config: FirewallZoneInput, site_id: str | None = None) -> Any:
    """Create a firewall zone (name + networkIds)."""
    return await _api("POST", f"/v1/sites/{await _site(site_id)}/firewall/zones", body=config.model_dump(exclude_none=True))


@tool(idempotent=True)
async def unifi_update_firewall_zone(zone_id: str, config: FirewallZoneInput, site_id: str | None = None) -> Any:
    """Update a firewall zone. PUT semantics — send the full config."""
    return await _api("PUT", f"/v1/sites/{await _site(site_id)}/firewall/zones/{zone_id}", body=config.model_dump(exclude_none=True))


@tool(destructive=True)
async def unifi_delete_firewall_zone(zone_id: str, site_id: str | None = None) -> Any:
    """Delete a firewall zone. System zones (Gateway, Internal, External, Hotspot, VPN, DMZ) cannot be deleted."""
    return await _api("DELETE", f"/v1/sites/{await _site(site_id)}/firewall/zones/{zone_id}")


# ── Firewall Policies (zone-based firewall) ──


@tool(read_only=True)
async def unifi_list_firewall_policies(site_id: str | None = None, offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List zone-based firewall policies at a site."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/firewall/policies", params=_page(offset, limit, filter))


@tool(read_only=True)
async def unifi_get_firewall_policy(policy_id: str, site_id: str | None = None) -> Any:
    """Get detailed info for a single firewall policy."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/firewall/policies/{policy_id}")


@tool()
async def unifi_create_firewall_policy(config: dict, site_id: str | None = None) -> Any:
    """Create a zone-based firewall policy. config: name, action (ALLOW|BLOCK|REJECT), source/destination
    (zoneId + optional matching), protocol, enabled — copy an existing policy via unifi_get_firewall_policy for the full shape."""
    return await _api("POST", f"/v1/sites/{await _site(site_id)}/firewall/policies", body=config)


@tool(idempotent=True)
async def unifi_update_firewall_policy(policy_id: str, config: dict, site_id: str | None = None) -> Any:
    """Update a firewall policy. PUT semantics — send the full config."""
    return await _api("PUT", f"/v1/sites/{await _site(site_id)}/firewall/policies/{policy_id}", body=config)


@tool(destructive=True)
async def unifi_delete_firewall_policy(policy_id: str, site_id: str | None = None) -> Any:
    """Delete a firewall policy."""
    return await _api("DELETE", f"/v1/sites/{await _site(site_id)}/firewall/policies/{policy_id}")


@tool(read_only=True)
async def unifi_get_firewall_policy_ordering(source_zone_id: str, destination_zone_id: str, site_id: str | None = None) -> Any:
    """Get firewall policy evaluation order for a source→destination zone pair."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/firewall/policies/ordering", params={"sourceFirewallZoneId": source_zone_id, "destinationFirewallZoneId": destination_zone_id})


@tool(idempotent=True)
async def unifi_set_firewall_policy_ordering(source_zone_id: str, destination_zone_id: str, policy_ids: list[str], site_id: str | None = None) -> Any:
    """Set firewall policy evaluation order for a zone pair (ordered list of policy IDs)."""
    return await _api("PUT", f"/v1/sites/{await _site(site_id)}/firewall/policies/ordering", params={"sourceFirewallZoneId": source_zone_id, "destinationFirewallZoneId": destination_zone_id}, body=policy_ids)


# ── ACL Rules ──


@tool(read_only=True)
async def unifi_list_acl_rules(site_id: str | None = None, offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List ACL rules at a site. Lower index = higher priority."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/acl-rules", params=_page(offset, limit, filter))


@tool(read_only=True)
async def unifi_get_acl_rule(rule_id: str, site_id: str | None = None) -> Any:
    """Get detailed info for a single ACL rule."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/acl-rules/{rule_id}")


@tool()
async def unifi_create_acl_rule(config: AclRuleConfig, site_id: str | None = None) -> Any:
    """Create an ACL rule (name, type IPV4|MAC, action ALLOW|BLOCK, index, source/destination filters)."""
    return await _api("POST", f"/v1/sites/{await _site(site_id)}/acl-rules", body=config.model_dump(exclude_none=True))


@tool(idempotent=True)
async def unifi_update_acl_rule(rule_id: str, config: AclRuleConfig, site_id: str | None = None) -> Any:
    """Update an ACL rule. PUT semantics — send the full config."""
    return await _api("PUT", f"/v1/sites/{await _site(site_id)}/acl-rules/{rule_id}", body=config.model_dump(exclude_none=True))


@tool(destructive=True)
async def unifi_delete_acl_rule(rule_id: str, site_id: str | None = None) -> Any:
    """Delete an ACL rule."""
    return await _api("DELETE", f"/v1/sites/{await _site(site_id)}/acl-rules/{rule_id}")


@tool(read_only=True)
async def unifi_get_acl_ordering(site_id: str | None = None) -> Any:
    """Get the ACL rule evaluation order."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/acl-rules/ordering")


@tool(idempotent=True)
async def unifi_set_acl_ordering(rule_ids: list[str], site_id: str | None = None) -> Any:
    """Set the ACL rule evaluation order (ordered list of rule IDs)."""
    return await _api("PUT", f"/v1/sites/{await _site(site_id)}/acl-rules/ordering", body=rule_ids)


# ── DNS Policies ──


@tool(read_only=True)
async def unifi_list_dns_policies(site_id: str | None = None, offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List DNS policies at a site."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/dns/policies", params=_page(offset, limit, filter))


@tool(read_only=True)
async def unifi_get_dns_policy(policy_id: str, site_id: str | None = None) -> Any:
    """Get detailed info for a single DNS policy."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/dns/policies/{policy_id}")


@tool()
async def unifi_create_dns_policy(config: dict, site_id: str | None = None) -> Any:
    """Create a DNS policy — copy an existing one via unifi_get_dns_policy for the full shape."""
    return await _api("POST", f"/v1/sites/{await _site(site_id)}/dns/policies", body=config)


@tool(idempotent=True)
async def unifi_update_dns_policy(policy_id: str, config: dict, site_id: str | None = None) -> Any:
    """Update a DNS policy. PUT semantics — send the full config."""
    return await _api("PUT", f"/v1/sites/{await _site(site_id)}/dns/policies/{policy_id}", body=config)


@tool(destructive=True)
async def unifi_delete_dns_policy(policy_id: str, site_id: str | None = None) -> Any:
    """Delete a DNS policy."""
    return await _api("DELETE", f"/v1/sites/{await _site(site_id)}/dns/policies/{policy_id}")


# ── Traffic Matching Lists ──


@tool(read_only=True)
async def unifi_list_traffic_matching_lists(site_id: str | None = None, offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List traffic matching lists (port/IP groups for ACLs) at a site."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/traffic-matching-lists", params=_page(offset, limit, filter))


@tool(read_only=True)
async def unifi_get_traffic_matching_list(list_id: str, site_id: str | None = None) -> Any:
    """Get detailed info for a single traffic matching list."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/traffic-matching-lists/{list_id}")


@tool()
async def unifi_create_traffic_matching_list(config: TrafficMatchingListConfig, site_id: str | None = None) -> Any:
    """Create a traffic matching list (name, type PORTS|IPV4_ADDRESSES|IPV6_ADDRESSES, items)."""
    return await _api("POST", f"/v1/sites/{await _site(site_id)}/traffic-matching-lists", body=config.model_dump(exclude_none=True))


@tool(idempotent=True)
async def unifi_update_traffic_matching_list(list_id: str, config: TrafficMatchingListConfig, site_id: str | None = None) -> Any:
    """Update a traffic matching list. PUT semantics — send the full config."""
    return await _api("PUT", f"/v1/sites/{await _site(site_id)}/traffic-matching-lists/{list_id}", body=config.model_dump(exclude_none=True))


@tool(destructive=True)
async def unifi_delete_traffic_matching_list(list_id: str, site_id: str | None = None) -> Any:
    """Delete a traffic matching list."""
    return await _api("DELETE", f"/v1/sites/{await _site(site_id)}/traffic-matching-lists/{list_id}")


# ── Switching (read-only) ──


@tool(read_only=True)
async def unifi_list_switch_stacks(site_id: str | None = None, offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List switch stacks at a site."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/switching/switch-stacks", params=_page(offset, limit, filter))


@tool(read_only=True)
async def unifi_get_switch_stack(stack_id: str, site_id: str | None = None) -> Any:
    """Get detailed info for a single switch stack."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/switching/switch-stacks/{stack_id}")


@tool(read_only=True)
async def unifi_list_mc_lag_domains(site_id: str | None = None, offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List MC-LAG domains at a site."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/switching/mc-lag-domains", params=_page(offset, limit, filter))


@tool(read_only=True)
async def unifi_get_mc_lag_domain(domain_id: str, site_id: str | None = None) -> Any:
    """Get detailed info for a single MC-LAG domain."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/switching/mc-lag-domains/{domain_id}")


@tool(read_only=True)
async def unifi_list_lags(site_id: str | None = None, offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List link aggregation groups (LAGs) at a site."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/switching/lags", params=_page(offset, limit, filter))


@tool(read_only=True)
async def unifi_get_lag(lag_id: str, site_id: str | None = None) -> Any:
    """Get detailed info for a single LAG."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/switching/lags/{lag_id}")


# ── Supporting Resources (read-only) ──


@tool(read_only=True)
async def unifi_list_wans(site_id: str | None = None, offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List WAN interfaces at a site."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/wans", params=_page(offset, limit, filter))


@tool(read_only=True)
async def unifi_list_vpn_tunnels(site_id: str | None = None, offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List site-to-site VPN tunnels at a site."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/vpn/site-to-site-tunnels", params=_page(offset, limit, filter))


@tool(read_only=True)
async def unifi_list_vpn_servers(site_id: str | None = None, offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List VPN servers at a site."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/vpn/servers", params=_page(offset, limit, filter))


@tool(read_only=True)
async def unifi_list_radius_profiles(site_id: str | None = None, offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List RADIUS profiles at a site."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/radius/profiles", params=_page(offset, limit, filter))


@tool(read_only=True)
async def unifi_list_device_tags(site_id: str | None = None, offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List device tags at a site (used for WiFi broadcasting filters)."""
    return await _api("GET", f"/v1/sites/{await _site(site_id)}/device-tags", params=_page(offset, limit, filter))


@tool(read_only=True)
async def unifi_list_dpi_categories(offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List DPI categories (global, not site-scoped)."""
    return await _api("GET", "/v1/dpi/categories", params=_page(offset, limit, filter))


@tool(read_only=True)
async def unifi_list_dpi_applications(offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List DPI applications (global, ~2100 entries — use filter/pagination)."""
    return await _api("GET", "/v1/dpi/applications", params=_page(offset, limit, filter))


@tool(read_only=True)
async def unifi_list_countries(offset: int = 0, limit: int = 25, filter: str | None = None) -> Any:
    """List countries for regulatory config (global)."""
    return await _api("GET", "/v1/countries", params=_page(offset, limit, filter))
