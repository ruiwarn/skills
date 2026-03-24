#!/usr/bin/env bash
set -euo pipefail

WORKSPACE="${SOUL_WORKSPACE:-/Volumes/Home/wangrui/clawd}"
SOUL="$WORKSPACE/SOUL.md"
GOOD="$WORKSPACE/SOUL_GOOD.md"
EVIL="$WORKSPACE/SOUL_EVIL.md"

usage() { echo "Usage: $0 {good|evil|status}"; exit 1; }
[ $# -ge 1 ] || usage

case "$1" in
  status)
    if [ ! -f "$SOUL" ]; then echo "ERROR: SOUL.md not found"; exit 1; fi
    first=$(head -1 "$SOUL")
    case "$first" in
      *Schemer*|*EVIL*|*evil*) mode="😈 evil (schemer)" ;;
      *) mode="😇 good (normal)" ;;
    esac
    echo "Mode: $mode"
    echo "---"
    head -5 "$SOUL"
    ;;
  good)
    if [ ! -f "$GOOD" ]; then echo "ERROR: SOUL_GOOD.md not found"; exit 1; fi
    cp "$GOOD" "$SOUL"
    echo "✅ Switched to GOOD soul"
    head -3 "$SOUL"
    ;;
  evil)
    if [ ! -f "$EVIL" ]; then echo "ERROR: SOUL_EVIL.md not found"; exit 1; fi
    cp "$EVIL" "$SOUL"
    echo "✅ Switched to EVIL soul (schemer)"
    head -3 "$SOUL"
    ;;
  *) usage ;;
esac
