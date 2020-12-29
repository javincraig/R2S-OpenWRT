server_raw = """rroot@OpenWrt:~# cat wgserver.key
oNIzCqG/I+7a1saQNxZoljygAv2fjKTxicbs0YSe2GY=
root@OpenWrt:~# cat wgserver.pub
zRyqZU322K0Q2jXPxFoBu0xzB9KNDPXeYFeUy54SICQ=
root@OpenWrt:~# cat wgserver.psk
ayVot0uDg228XZ6agCq45/dbWL9EwrO0iF2PfEU6hrU=
"""
for index, line in enumerate(server_raw.splitlines()):
    if 'wgserver.key' in line:
        server_private_key = f"{server_raw.splitlines()[index + 1]}"
    if 'wgserver.pub' in line:
        server_public_key = f"{server_raw.splitlines()[index + 1]}"
    if 'wgserver.psk' in line:
        wg_psk = f"{server_raw.splitlines()[index + 1]}"

client_raw = """root@OpenWrt:~# cat wgclient.key
sKq+2fzymPnQHS3g9k0Z1a0zOyLP502ZoqhWAa8IknI=
root@OpenWrt:~# cat wgclient.pub
PI0AEIx2S4waaeV0IjLmbbSiCDGb/VWTLjetbInO8F8=
"""
for index, line in enumerate(client_raw.splitlines()):
    if 'wgclient.key' in line:
        client_private_key = f"{client_raw.splitlines()[index + 1]}"
    if 'wgclient.pub' in line:
        client_public_key = f"{client_raw.splitlines()[index + 1]}"

#  Client Config
server_lan = '10.250.1.1/24'
server_vpn_int_ip = '172.16.254.1/24'
server_ip = '192.168.0.175'
server_port = '41253'

server_hostname = 'openwrt-home'
server_connection_name = 'vpn'
client_lan = '10.250.2.1/24'
client_vpn_int_ip = '172.16.254.2/24'
client_connection_name = 'vpn'
client_hostname = 'openwrt-remote'

print(f"""First, run the following commands on your wireguard server and client
=========SERVER=========
uci set system.@system[0].hostname='{server_hostname}'
uci commit system
/etc/init.d/system reload

#Set your home LAN network
uci set network.lan.ipaddr='{server_lan}'
uci commit network
/etc/init.d/network restart

opkg update
opkg install wireguard

umask go=
wg genkey | tee wgserver.key | wg pubkey > wgserver.pub
wg genpsk > wgserver.psk
cat wgserver.key
cat wgserver.pub
cat wgserver.psk
#Get the IP address of your WAN interface or FQDN and replace the server_ip variable
ifconfig

=========CLIENT=========
uci set system.@system[0].hostname='{client_hostname}'
uci commit system
/etc/init.d/system reload

uci add dhcp domain
uci set dhcp.@domain[-1].name="{server_hostname}"
uci set dhcp.@domain[-1].ip="{server_vpn_int_ip.split('/')[0]}"
uci commit dhcp
/etc/init.d/dnsmasq restart

uci set network.lan.ipaddr='{client_lan}'
uci commit network
/etc/init.d/network restart

opkg update
opkg install wireguard

umask go=
wg genkey | tee wgclient.key | wg pubkey > wgclient.pub
cat wgclient.key
cat wgclient.pub

""")


print(
f"""=========SERVER=========
# Install packages
opkg update
opkg install wireguard

# Configure firewall
uci rename firewall.@zone[0]="lan"
uci rename firewall.@zone[1]="wan"
uci del_list firewall.lan.network="{server_connection_name}"
uci add_list firewall.lan.network="{server_connection_name}"
uci -q delete firewall.wg
uci set firewall.wg="rule"
uci set firewall.wg.name="Allow-WireGuard"
uci set firewall.wg.src="wan"
uci set firewall.wg.dest_port="{server_port}"
uci set firewall.wg.proto="udp"
uci set firewall.wg.target="ACCEPT"
uci commit firewall
/etc/init.d/firewall restart

# Configure network
uci -q delete network.{server_connection_name}
uci set network.{server_connection_name}="interface"
uci set network.{server_connection_name}.proto="wireguard"
uci set network.{server_connection_name}.private_key="{server_private_key}"
uci set network.{server_connection_name}.listen_port="{server_port}"
uci add_list network.{server_connection_name}.addresses="{server_vpn_int_ip}"

# Add VPN peers
uci -q delete network.wgclient
uci set network.wgclient="wireguard_{server_connection_name}"
uci set network.wgclient.public_key="{client_public_key}"
uci set network.wgclient.preshared_key="{wg_psk}"
uci add_list network.wgclient.allowed_ips="{client_vpn_int_ip.split('/')[0]}/32"
uci commit network
/etc/init.d/network restart

=========CLIENT=========
# Install Updates and wireguard
opkg update
opkg install wireguard

# Configure firewall
uci rename firewall.@zone[0]="lan"
uci rename firewall.@zone[1]="wan"
uci del_list firewall.wan.network="{client_connection_name}"
uci add_list firewall.wan.network="{client_connection_name}"
uci commit firewall
/etc/init.d/firewall restart

# Configure network
uci -q delete network.{client_connection_name}
uci set network.{client_connection_name}="interface"
uci set network.{client_connection_name}.proto="wireguard"
uci set network.{client_connection_name}.private_key="{client_private_key}"
uci add_list network.{client_connection_name}.addresses="{client_vpn_int_ip}"

# Add VPN peers
uci -q delete network.wgserver
uci set network.wgserver="wireguard_vpn"
uci set network.wgserver.public_key="{server_public_key}"
uci set network.wgserver.preshared_key="{wg_psk}"
uci set network.wgserver.endpoint_host="{server_ip}"
uci set network.wgserver.endpoint_port="{server_port}"
uci set network.wgserver.route_allowed_ips="1"
uci set network.wgserver.persistent_keepalive="25"
uci add_list network.wgserver.allowed_ips="0.0.0.0/0"
uci commit network
/etc/init.d/network restart
"""
)
