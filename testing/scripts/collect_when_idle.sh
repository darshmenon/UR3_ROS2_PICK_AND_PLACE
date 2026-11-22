#!/bin/bash
# Wait until machine load is low (<20 for 3 checks 60 s apart), then run collect_mtc_demos.sh.
# Prerequisites: same as collect_mtc_demos.sh.
# Output goes to testing/_out/ (gitignored). Run from anywhere.
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
mkdir -p "$REPO_ROOT/testing/_out"
ok=0
while [ $ok -lt 3 ]; do
  l=$(cut -d. -f1 /proc/loadavg)
  if [ "$l" -lt 20 ]; then ok=$((ok+1)); else ok=0; fi
  sleep 60
done
"$REPO_ROOT/testing/scripts/collect_mtc_demos.sh" > "$REPO_ROOT/testing/_out/mtc_demos.log" 2>&1
