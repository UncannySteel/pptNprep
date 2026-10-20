#!/bin/sh
# Runs guard.py with the first working Python on PATH (python3, python, py).
# If none works, the tool call is blocked (exit 2) rather than left unguarded.
dir=$(dirname "$0")
for py in python3 python py; do
  if "$py" -S -c "" >/dev/null 2>&1; then
    exec "$py" "$dir/guard.py" "$@"
  fi
done
echo "pptNprep guard: no working Python found on PATH, so this call is blocked. Install Python or fix PATH." >&2
exit 2
