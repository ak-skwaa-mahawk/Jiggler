#!/usr/bin/env python3
import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

NFTABLES_CONTAINMENT_RULESET = """
table inet perimeter_guard {
    set admin_management_v4 {
        type ipv4_addr
        flags interval
        elements = { 127.0.0.1, 10.8.0.0/24 }
    }

    chain input_audit {
        type filter hook input priority filter; policy accept;

        # Block External Management Web Portals
        tcp dport { 80, 443, 8443, 9443 } ip saddr != @admin_management_v4 counter drop comment "Drop Unsanctioned Perimeter Web Access"

        # Block Unrestricted SNMP Exposure
        udp dport { 161, 162 } ip saddr != @admin_management_v4 counter drop comment "Restrict SNMP to Management Subnet"
        tcp dport { 161, 162 } ip saddr != @admin_management_v4 counter drop comment "Restrict TCP SNMP Exposure"
    }
}
"""

def sanitize_snmp_configuration():
    snmp_conf_path = "/etc/snmp/snmpd.conf"
    logging.info("Restricting SNMP access to local loopback/management vectors...")
    
    hardened_snmp_config = (
        "# Sovereign Hardened SNMP Daemon Config\n"
        "agentaddress 127.0.0.1:161\n"
        "com2sec localUser 127.0.0.1 internal_sec_token\n"
        "group localGroup usm localUser\n"
        "view allIncluded included .1\n"
        "access localGroup \"\" any noauth exact allIncluded none none\n"
    )
    
    try:
        if os.path.exists(os.path.dirname(snmp_conf_path)):
            with open(snmp_conf_path, "w") as f:
                f.write(hardened_snmp_config)
            logging.info("SNMP daemon configuration restricted.")
        else:
            logging.warning(f"Directory {os.path.dirname(snmp_conf_path)} not present. Skipping direct config write.")
    except Exception as e:
        logging.error(f"Failed to update SNMP configuration: {e}")

def apply_nftables_containment():
    logging.info("Applying nftables packet filtering rules...")
    try:
        process = subprocess.Popen(["nft", "-f", "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = process.communicate(input=NFTABLES_CONTAINMENT_RULESET)
        if process.returncode == 0:
            logging.info("NFTables perimeter containment active.")
        else:
            logging.warning(f"NFTables execution returned status code {process.returncode}: {stderr.strip()}")
    except FileNotFoundError:
        logging.warning("'nft' binary unavailable. Relying on user-space restrictions.")

if __name__ == "__main__":
    sanitize_snmp_configuration()
    apply_nftables_containment()
