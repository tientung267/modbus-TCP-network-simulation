#!/bin/bash
# firewall-rules.sh

# Check the current user
# echo "Running as user: $(whoami)"
# Create ip tables
nft add table ip proxy_firewall

# Create input chain in filer table to filter all incomming request
nft add chain ip proxy_firewall input { type filter hook input priority 0 \; }

# Only allow traffic from two container in bridge network
nft add rule ip proxy_firewall input ip saddr 172.20.0.10 accept
nft add rule ip proxy_firewall input ip saddr 172.20.0.12 accept
nft add rule ip proxy_firewall input ip saddr 172.20.0.0/16 drop

# logout ruleset
nft list ruleset

