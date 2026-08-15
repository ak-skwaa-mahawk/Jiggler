#!/usr/bin/env bash
set -e

echo "[+] Generating WireGuard keypairs for Cloud POP and Edge Appliance..."

# Generate Server Keys (fallback to python secrets if wg cli not present)
SERVER_PRIV=$(wg genkey 2>/dev/null || python3 -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())")
SERVER_PUB=$(echo "$SERVER_PRIV" | wg pubkey 2>/dev/null || echo "REPLACE_WITH_SERVER_PUBKEY")

# Generate Edge Keys
EDGE_PRIV=$(wg genkey 2>/dev/null || python3 -c "import secrets, base64; print(base64.b64encode(secrets.token_bytes(32)).decode())")
EDGE_PUB=$(echo "$EDGE_PRIV" | wg pubkey 2>/dev/null || echo "REPLACE_WITH_EDGE_PUBKEY")

echo "[+] Server Public Key : $SERVER_PUB"
echo "[+] Edge Public Key   : $EDGE_PUB"

cat << CONF_EOF > ~/Tordial-GS-_Manifold/deploy/server_wg0.conf
[Interface]
Address = 10.51.82.1/31
ListenPort = 51820
PrivateKey = $SERVER_PRIV
MTU = 1420
PostUp = sysctl -w net.ipv4.ip_forward=1 && iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE && iptables -A FORWARD -i wg0 -j ACCEPT && iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu
PostDown = iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE && iptables -D FORWARD -i wg0 -j ACCEPT && iptables -t mangle -D FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu

[Peer]
PublicKey = $EDGE_PUB
AllowedIPs = 10.51.82.2/32
CONF_EOF

cat << CONF_EOF > ~/Tordial-GS-_Manifold/deploy/edge_wg0.conf
[Interface]
Address = 10.51.82.2/31
PrivateKey = $EDGE_PRIV
MTU = 1420
Table = 51820

[Peer]
PublicKey = $SERVER_PUB
Endpoint = YOUR_CLOUD_IP:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25
CONF_EOF

echo "[+] Configs successfully generated in deploy/server_wg0.conf and deploy/edge_wg0.conf"
