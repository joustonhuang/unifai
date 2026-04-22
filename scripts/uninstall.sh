#!/usr/bin/env bash
set -euo pipefail

echo "== Uninstall helper =="

cat <<EOF2
Bundled local runtime assets have been removed from this repository.

There is no repository-managed runtime to uninstall anymore.
If you previously installed external model runtimes or services, remove them
using their own host-native service manager or package workflow.
EOF2
