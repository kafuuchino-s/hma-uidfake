#!/system/bin/sh
# SPDX-License-Identifier: GPL-2.0
# No loader fallback: an early-load failure remains visible and is not retried.
umask 077
MODDIR=$(dirname "$0")
. "$MODDIR/common.sh"
[ ! -e "$MODDIR/disable" ] && [ ! -e "$MODDIR/remove" ] || exit 0
mkdir -p "$MODDIR/state" || exit 1
chmod 0700 "$MODDIR/state"
exec 9>"$MODDIR/state/sync.lock"
"$BB" flock -n 9 || exit 0
exec >>"$MODDIR/state/sync.log" 2>&1
BOOT=$(cat /proc/sys/kernel/random/boot_id) || exit 1
echo "[service] boot=$BOOT wait for Android framework"
while [ "$(getprop sys.boot_completed)" != 1 ]; do sleep 1; done
[ "$(cat "$MODDIR/state/boot_id" 2>/dev/null)" = "$BOOT" ] || { echo '[service] no early-load receipt for this boot'; exit 1; }
kernel_bound && module_live && hooks_ready || { echo '[service] no complete early hook set; not loading or retrying'; exit 1; }
printf '%s\n' "$$" >"$MODDIR/state/sync.pid"
echo "[service] exec author sync-tool pid=$$ mode=watch"
# No --once, --template or --write-config: original config/package watching mode.
exec "$MODDIR/sync-tool"
