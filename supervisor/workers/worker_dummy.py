#!/usr/bin/env python3
# Minimal host-native worker used for Gaia runtime validation.
# This proves:
#   - Gaia can spawn a worker process
#   - runtime environment variables are wired correctly
#   - logs are emitted continuously for supervision tests

import os
import time
from datetime import datetime

def main():
    print("[worker_dummy] started")
    print(f"[worker_dummy] uid={os.getuid()} gid={os.getgid()}")
    print(f"[worker_dummy] cwd={os.getcwd()}")
    print(f"[worker_dummy] TZ={os.environ.get('TZ','(not set)')}")
    while True:
        print(f"[worker_dummy] heartbeat {datetime.now().isoformat(timespec='seconds')}")
        time.sleep(5)

if __name__ == "__main__":
    main()
