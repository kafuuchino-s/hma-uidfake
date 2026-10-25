#!/system/bin/sh
# SPDX-License-Identifier: GPL-2.0
# Bound to the parent's frozen tablet kernel; no MIX4 approval is inherited.
EXPECTED_NOTES_SHA=f97c09b8e6c902eb05b9365dd9010493b324398effb7d6986f82a1d6cb5859d1
EXPECTED_SOURCE_CONFIG_SHA=ffa1642d8ca8b3e71362a135e28bbec81c99ae307c3b1aaed86b7a29619d0d09
EXPECTED_VISIBLE_CONFIG_SHA=197c535c9ba32d8123f2edeba143c09afe8acf6ee8af801d2e0b91e4291fa279
BB=/data/adb/ksu/bin/busybox

kernel_bound() {
  [ -x "$BB" ] || { echo "binding: KernelSU busybox missing"; return 1; }
  _notes=$("$BB" sha256sum /sys/kernel/notes) || return 1
  _notes=$(printf '%s\n' "$_notes" | "$BB" awk '{print $1}')
  [ "$_notes" = "$EXPECTED_NOTES_SHA" ] || { echo "binding: kernel notes mismatch"; return 1; }
  _config=$("$BB" zcat /proc/config.gz | "$BB" sha256sum) || return 1
  _config=$(printf '%s\n' "$_config" | "$BB" awk '{print $1}')
  [ "$_config" = "$EXPECTED_VISIBLE_CONFIG_SHA" ] || { echo "binding: visible kernel config view mismatch"; return 1; }
  # kallsyms_lookup_name is a normal GPL import checked by the native loader.
  # module_init validates all 22 required core symbols before any publication.
  return 0
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
          v["lsm_state"]==1 && v["lsm_error"]==0 && v["native"]==4 && v["compat"]==4);
      exit !ok
    }' "$MODDIR/state/hook-status.json"
}
