#!/system/bin/sh
# SPDX-License-Identifier: GPL-2.0
umask 077
MODDIR=$(dirname "$0")
. "$MODDIR/common.sh"
[ ! -e "$MODDIR/disable" ] && [ ! -e "$MODDIR/remove" ] || exit 0
mkdir -p "$MODDIR/state" || exit 1
chmod 0700 "$MODDIR/state"
exec 9>"$MODDIR/state/load.lock"
"$BB" flock -n 9 || exit 0
BOOT=$(cat /proc/sys/kernel/random/boot_id) || exit 1
[ "$(cat "$MODDIR/state/load-attempt" 2>/dev/null)" != "$BOOT" ] || exit 0
printf '%s\n' "$BOOT" >"$MODDIR/state/load-attempt"
printf '%s\n' "$BOOT" >"$MODDIR/state/boot_id"
exec >>"$MODDIR/state/load.log" 2>&1
echo "[post-fs-data] boot=$BOOT time=$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
kernel_bound && payloads_bound || { echo '[load] refused: binding failed'; exit 1; }
if module_live; then
  echo '[load] already present; no second load attempt'
  exit 0
fi
"$MODDIR/load-ko" "$MODDIR/ko/hma_uidfake.ko"
RC=$?
echo "[load] finit_module flags=0 rc=$RC"
[ "$RC" -eq 0 ] && module_live && hooks_ready || { echo '[load] failed or hooks incomplete'; exit 1; }
echo '[load] normal load and hooks verified'
