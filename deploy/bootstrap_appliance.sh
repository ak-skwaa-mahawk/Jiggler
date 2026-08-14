#!/usr/bin/env bash
# ==============================================================================
# Tordial Routing Protocol (TRP) - Sovereign Edge Appliance Bootstrap
# Target OS: Debian 12 (Bookworm) / Ubuntu Server (Bare-Metal x86_64 or ARM64)
# ==============================================================================
set -euo pipefail

echo "=========================================================="
echo "  PROVISIONING TORDIAL SOVEREIGN ROUTER APPLIANCE"
echo "=========================================================="

if [ "$EUID" -ne 0 ]; then
  echo "[!] Must run as root (e.g. sudo bash bootstrap_appliance.sh)"
  exit 1
fi

# 1. Base Networking & Dependencies
echo "[+] Installing system packages..."
apt-get update -qy
DEBIAN_FRONTEND=noninteractive apt-get install -qy \
    python3 \
    python3-pip \
    python3-numpy \
    iproute2 \
    nftables \
    wireguard \
    unbound \
    ethtool \
    git \
    sqlite3

# 2. Kernel Sysctl Parameters (BBR + CAKE + IP Forwarding)
echo "[+] Writing /etc/sysctl.d/99-tordial-router.conf..."
cat << 'SYSCTL_EOF' > /etc/sysctl.d/99-tordial-router.conf
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
net.core.default_qdisc = cake
net.ipv4.tcp_congestion_control = bbr
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216
SYSCTL_EOF
sysctl -p /etc/sysctl.d/99-tordial-router.conf

# 3. Sovereign Firewall Ruleset
echo "[+] Configuring /etc/nftables.conf..."
cat << 'NFT_EOF' > /etc/nftables.conf
#!/usr/sbin/nft -f
flush ruleset

table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;
        ct state established,related accept
        iif "lo" accept
        iifname "eth1" accept
        iifname "br0" accept
        ct state invalid drop
    }

    chain forward {
        type filter hook forward priority 0; policy drop;
        iifname "eth1" oifname "eth0" accept
        iifname "eth1" oifname "wg0" accept
        iifname "eth0" oifname "eth1" ct state established,related accept
        iifname "wg0" oifname "eth1" ct state established,related accept
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}

table ip nat {
    chain postrouting {
        type nat hook postrouting priority 100; policy accept;
        oifname "eth0" masquerade
        oifname "wg0" masquerade
    }
}
NFT_EOF
systemctl enable --now nftables

# 4. Deploy TRP Daemon to /opt/tordial-router
echo "[+] Deploying TRP control plane to /opt/tordial-router..."
INSTALL_DIR="/opt/tordial-router"
mkdir -p "$INSTALL_DIR/tools"

if [ -d "./tools" ]; then
    cp -r ./tools/* "$INSTALL_DIR/tools/"
    cp ./sovereign_router.yaml "$INSTALL_DIR/" || true
else
    git clone https://github.com/ak-skwaa-mahawk/Jiggler.git "$INSTALL_DIR"
fi

# 5. Systemd Service Setup
echo "[+] Installing tordial-routed.service..."
cat << 'SERVICE_EOF' > /etc/systemd/system/tordial-routed.service
[Unit]
Description=Tordial Routing Protocol (TRP) Control Plane Daemon
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tordial-router
ExecStart=/usr/bin/python3 /opt/tordial-router/tools/tordial_routed.py
Restart=always
RestartSec=2
LimitNOFILE=65535

[Install]
WantedBy=multi-user.target
SERVICE_EOF

systemctl daemon-reload
systemctl enable --now tordial-routed.service

echo "=========================================================="
echo "  TORDIAL SOVEREIGN APPLIANCE PROVISIONING COMPLETE"
echo "  Check status: systemctl status tordial-routed"
echo "=========================================================="
