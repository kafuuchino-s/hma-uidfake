#!/system/bin/sh
# SPDX-License-Identifier: GPL-2.0
# Only the exact kernel whose final CFI table and normal imports were audited.
EXPECTED_NOTES_SHA=2860d6481e7bb3ece42a4fb675d4c682e803e6dcf4bbd6e38d2143a98926f724
EXPECTED_CONFIG_SHA=9751e53f21287e8a75b3338eb34172dcd19692e58fc6a6c39da77c7259bb0516
BB=/data/adb/ksu/bin/busybox

kernel_bound() {
  [ -x "$BB" ] || { echo "binding: KernelSU busybox missing"; return 1; }
  _notes=$("$BB" sha256sum /sys/kernel/notes) || return 1
  _notes=$(printf '%s\n' "$_notes" | "$BB" awk '{print $1}')
  [ "$_notes" = "$EXPECTED_NOTES_SHA" ] || { echo "binding: kernel notes mismatch"; return 1; }
  _config=$("$BB" zcat /proc/config.gz | "$BB" sha256sum) || return 1
  _config=$(printf '%s\n' "$_config" | "$BB" awk '{print $1}')
  [ "$_config" = "$EXPECTED_CONFIG_SHA" ] || { echo "binding: kernel config mismatch"; return 1; }
}

payloads_bound() {
  (cd "$MODDIR" && "$BB" sha256sum -c payload.sha256)
}

module_live() {
  "$BB" grep -q '^hma_uidfake .* Live ' /proc/modules
}

hooks_ready() {
  "$MODDIR/kauxctl" --status >"$MODDIR/state/hook-status.json" || return 1
  "$BB" awk 'BEGIN { RS=","; FS=":" }
    { gsub(/[^a-z_]/, "", $1); v[$1]=$2+0 }
    END {
      ok=(v["magic"]==2020958571 && v["size"]==104 && v["version"]==3 &&
          v["va_bits"]==39 && v["page_shift"]==12 && v["flags"]%8==7 &&
          v["native"]==v["native_expected"] && v["compat"]==v["compat_expected"] &&
          v["last_error"]==0 &&
          ((v["lsm_state"]==1 && v["lsm_error"]==0 && v["native"]==4 && v["compat"]==4) ||
           (v["lsm_state"]==3 && v["native"]==10 && v["compat"]==10)));
      exit !ok
    }' "$MODDIR/state/hook-status.json"
}
