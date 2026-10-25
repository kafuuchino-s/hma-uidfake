#!/system/bin/sh
# SPDX-License-Identifier: GPL-2.0
MODDIR=$(dirname "$0")
. "$MODDIR/common.sh"
if ! module_live; then
  echo 'Module not loaded; inspect state/load.log. A normal reboot is required.'
  [ ! -f "$MODDIR/state/load.log" ] || "$BB" tail -n 12 "$MODDIR/state/load.log"
  exit 1
fi
exec "$MODDIR/kauxctl" --status
