#!/usr/bin/env bash
set -euo pipefail

echo "== Stage 25: Logging (journald persistent + log directories) =="

# 1) Create standard log directories for little7
sudo mkdir -p /var/log/little7/supervisor
sudo chmod 0755 /var/log/little7
sudo chmod 0755 /var/log/little7/supervisor

# 2) Configure journald to persist logs across reboots (drop-in config)
sudo mkdir -p /etc/systemd/journald.conf.d
sudo tee /etc/systemd/journald.conf.d/little7.conf > /dev/null <<'EOF'

[Journal]
Storage=persistent
SystemMaxUse=512M
SystemMaxFileSize=64M
MaxRetentionSec=14day
Compress=yes
EOF

# 3) Restart journald to apply changes
sudo systemctl restart systemd-journald

# 4) Quick verification output (non-fatal)
echo "[INFO] journald disk usage:"
sudo journalctl --disk-usage || true

echo "[INFO] log directories:"
ls -ald /var/log/little7 /var/log/little7/supervisor || true

echo "Stage 25 complete."
