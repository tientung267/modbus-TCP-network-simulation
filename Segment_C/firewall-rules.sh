#!/bin/bash
# firewall-rules.sh

# Check the current user
# echo "Running as user: $(whoami)"
# Create ip tables
nft add table ip server_firewall

# Create input chain in filer table to filter all incomming request
nft add chain ip server_firewall input { type filter hook input priority 0 \; }

# Only allow traffic from proxy-container in bridge network
nft add rule ip server_firewall input ip saddr 172.20.0.11 accept
nft add rule ip server_firewall input ip saddr 172.20.0.0/16 drop

# logout ruleset
nft list ruleset

