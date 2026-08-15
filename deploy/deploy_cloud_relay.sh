#!/usr/bin/env bash
# ==============================================================================
# Tordial Routing Protocol (TRP) - Cloud POP Relay Provisioner
# Target: Remote VPS running Debian 12 / Ubuntu 22.04+ (x86_64 or ARM64)
# ==============================================================================
set -euo pipefail

echo "=========================================================="
echo "  PROVISIONING TORDIAL CLOUD WIREGUARD SCRUBBING POP     "
echo "=========================================================="

if [ "$EUID" -ne 0 ]; then
  echo "[!] Error: Must run as root (use sudo bash deploy_cloud_relay.sh)"
  exit 1
fi

# Detect Public WAN Interface
WAN_IF=$(ip -4 route show default | awk '{print $5}' | head -n 1)
if [ -z "$WAN_IF" ]; then
    WAN_IF="eth0"
fi
PUBLIC_IP=$(curl -4 -s https://ifconfig.me || ip -4 addr show dev "$WAN_IF" | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -n 1)

echo "[+] WAN Interface Detected: $WAN_IF"
echo "[+] Public IP Detected    : $PUBLIC_IP"

# 1. Update and install dependencies
echo "[+] Installing WireGuard and kernel networking tools..."
apt-get update -qy
DEBIAN_FRONTEND=noninteractive apt-get install -qy \
    wireguard \
    wireguard-tools \
    iptables \
    iproute2 \
    curl

# 2. Apply High-Throughput & Low-Jitter Kernel Parameters
echo "[+] Configuring sysctl parameters for BBR and forwarding..."
cat << 'SYSCTL_EOF' > /etc/sysctl.d/99-tordial-relay.conf
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
net.core.default_qdisc = cake
net.ipv4.tcp_congestion_control = bbr
net.core.netdev_max_backlog = 10000
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
SYSCTL_EOF
sysctl -p /etc/sysctl.d/99-tordial-relay.conf >/dev/null

# 3. Generate WireGuard Cryptographic Keypairs
echo "[+] Generating Server and Client keypairs..."
mkdir -p /etc/wireguard
chmod 700 /etc/wireguard

SERVER_PRIV=$(wg genkey)
SERVER_PUB=$(echo "$SERVER_PRIV" | wg pubkey)
CLIENT_PRIV=$(wg genkey)
CLIENT_PUB=$(echo "$CLIENT_PRIV" | wg pubkey)

# 4. Generate Server Configuration (/etc/wireguard/wg0.conf)
echo "[+] Writing /etc/wireguard/wg0.conf..."
cat << WG_SERVER_EOF > /etc/wireguard/wg0.conf
[Interface]
Address = 10.51.82.1/31
ListenPort = 51820
PrivateKey = $SERVER_PRIV
MTU = 1420

# Forwarding, NAT Masquerade, and TCP MSS Clamping to PMTU
PostUp = iptables -t nat -A POSTROUTING -o $WAN_IF -j MASQUERADE
PostUp = iptables -A FORWARD -i wg0 -o $WAN_IF -j ACCEPT
PostUp = iptables -A FORWARD -i $WAN_IF -o wg0 -m state --state RELATED,ESTABLISHED -j ACCEPT
PostUp = iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu

PostDown = iptables -t nat -D POSTROUTING -o $WAN_IF -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -o $WAN_IF -j ACCEPT
PostDown = iptables -D FORWARD -i $WAN_IF -o wg0 -m state --state RELATED,ESTABLISHED -j ACCEPT
PostDown = iptables -t mangle -D FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu

[Peer]
# Edge Router / Local Appliance
PublicKey = $CLIENT_PUB
AllowedIPs = 10.51.82.2/32
WG_SERVER_EOF
chmod 600 /etc/wireguard/wg0.conf

# 5. Enable and Start WireGuard Server Interface
echo "[+] Starting WireGuard relay interface (wg0)..."
systemctl enable --now wg-quick@wg0
systemctl restart wg-quick@wg0

# 6. Generate Matching Edge Client Configuration File
cat << WG_CLIENT_EOF > /root/tordial_edge_wg0.conf
[Interface]
Address = 10.51.82.2/31
PrivateKey = $CLIENT_PRIV
MTU = 1420
Table = 51820

[Peer]
PublicKey = $SERVER_PUB
Endpoint = ${PUBLIC_IP}:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
WG_CLIENT_EOF

echo "=========================================================="
echo "  TORDIAL CLOUD POP PROVISIONING COMPLETE"
echo "=========================================================="
echo "  • Server WireGuard IP : 10.51.82.1/31"
echo "  • Listen Port         : 51820 UDP"
echo "  • WAN Interface       : $WAN_IF ($PUBLIC_IP)"
echo "----------------------------------------------------------"
echo "  EDGE CLIENT CONFIGURATION (Saved to /root/tordial_edge_wg0.conf):"
echo "----------------------------------------------------------"
cat /root/tordial_edge_wg0.conf
echo "=========================================================="
