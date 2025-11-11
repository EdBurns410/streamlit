#!/bin/bash
set -euo pipefail

iptables -P OUTPUT DROP || true
iptables -F OUTPUT || true
iptables -A OUTPUT -o lo -j ACCEPT || true
iptables -A OUTPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT || true

exec "$@"
