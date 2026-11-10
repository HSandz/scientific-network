#!/usr/bin/env bash
# Run on the inspected Ubuntu VM as its sudo-capable SSH user.
set -euo pipefail
if [[ $(. /etc/os-release; echo "$ID") != ubuntu ]]; then
  echo 'This bootstrap supports Ubuntu only.' >&2; exit 1
fi
# Use only the previously inspected OS filesystem. Never format a disk.
if ! swapon --noheadings --show | grep -q .; then
  if [[ -e /swapfile-scientific-network || -L /swapfile-scientific-network ]]; then
    echo 'Existing inactive swap path needs inspection; refusing replacement.' >&2; exit 1
  fi
  available=$(df --output=avail -B1 / | tail -1)
  (( available > 18 * 1024 * 1024 * 1024 )) || { echo 'Insufficient swap/deployment headroom.' >&2; exit 1; }
  sudo -n fallocate -l 4G /swapfile-scientific-network
  sudo -n chmod 600 /swapfile-scientific-network
  sudo -n mkswap /swapfile-scientific-network
  sudo -n swapon /swapfile-scientific-network
  if ! grep -q '^/swapfile-scientific-network ' /etc/fstab; then
    echo '/swapfile-scientific-network none swap sw,nofail 0 0' | sudo -n tee -a /etc/fstab >/dev/null
  fi
fi
if [[ ! -e /etc/sysctl.d/60-scientific-network.conf ]]; then
  echo 'vm.swappiness=10' | sudo -n tee /etc/sysctl.d/60-scientific-network.conf >/dev/null
  sudo -n sysctl -p /etc/sysctl.d/60-scientific-network.conf
fi
if ! command -v docker >/dev/null; then
  sudo -n apt-get update -qq
  sudo -n apt-get install -y --no-install-recommends ca-certificates curl
  sudo -n install -m 0755 -d /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo -n tee /etc/apt/keyrings/docker.asc >/dev/null
  sudo -n chmod a+r /etc/apt/keyrings/docker.asc
  . /etc/os-release
  printf 'deb [arch=%s signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu %s stable\n' "$(dpkg --print-architecture)" "$VERSION_CODENAME" | sudo -n tee /etc/apt/sources.list.d/docker.list >/dev/null
  sudo -n apt-get update -qq
  sudo -n apt-get install -y --no-install-recommends docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
fi
sudo -n systemctl enable --now docker
sudo -n docker version --format '{{.Server.Version}}'
sudo -n docker compose version
free -h
swapon --show
df -h /
