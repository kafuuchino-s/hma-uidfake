#!/system/bin/sh
# SPDX-License-Identifier: GPL-2.0
SKIPUNZIP=1
ui_print "- HMA UID Fake: elish 4.19 port for the exact bound kernel"
[ "$BOOTMODE" = true ] || abort "Install through the running KernelSU manager/ksud."
[ "$KSU" = true ] || abort "This package requires the validated KernelSU/BakaSU environment."
[ "$ARCH" = arm64 ] || abort "Only arm64 is supported."
[ "$API" -ge 33 ] || abort "Android API 33 or later is required."
unzip -o "$ZIPFILE" module.prop common.sh post-fs-data.sh service.sh action.sh uninstall.sh \
  ko/hma_uidfake.ko load-ko kauxctl sync-tool payload.sha256 package.json LICENSE NOTICE README.md ELISH.md skip_mount -d "$MODPATH" >&2 || abort "Extraction failed."
MODDIR="$MODPATH"
. "$MODDIR/common.sh"
kernel_bound || abort "Kernel notes/config do not match the audited target."
payloads_bound || abort "Payload SHA-256 mismatch."
"$BB" --list | "$BB" grep -qx flock || abort "KernelSU busybox flock is required."
set_perm_recursive "$MODPATH" 0 0 0755 0644
for f in common.sh post-fs-data.sh service.sh action.sh uninstall.sh; do set_perm "$MODPATH/$f" 0 0 0755; done
for f in load-ko kauxctl sync-tool; do set_perm "$MODPATH/$f" 0 0 0755; done
ui_print "- Files staged only; no module load or daemon was started."
ui_print "- Keep conflicting UID implementations disabled during activation."
ui_print "- Reboot normally to activate; detector testing remains manual."
