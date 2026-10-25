# HMA UID Fake — elish 4.19 port

The active local branch is `elish-4.19`. Read [ELISH.md](ELISH.md) and
[module/README.md](module/README.md) for its exact GPL-resolver kernel binding,
new tablet approval and standard package. The original MIX4 material below is
retained as historical reference; its approvals and commands target that device.

## Historical MIX4 5.4 reference

Maintenance fork: https://github.com/kafuuchino-s/hma-uidfake , branch mix4-5.4.

This port retains the history and GPL-2.0 code of KodateMitsuru and Anatdx. Its source baseline is Anatdx/hma-uidfake at dcc8c1993f355de083d1beca834da423c0ae2098. It targets one audited Xiaomi MIX4 BakaSU kernel; it is not a generic 5.4/KMI package.

## What this branch changes

The three-file 5.4 port maps old nofault/page helpers and replaces two unexported private function calls with a presence check under the native UID hash lock. CFI, shadow call stack, normal modversions and vermagic checks remain enabled. The five module translation units and headers match the tested candidate; the author HMA parser, rule expansion and watcher remain unchanged.

The package uses the normal finit_module(fd, "", 0) loader. It contains no SHN_ABS resolver or vermagic rewrite loader. The original loader submodule and active build/installation route have been removed from this branch; their upstream Git history remains.

## Install and operate

Install the locally validated ZIP with the normal BakaSU manager or ksud module install. Keep the old cq_uid_seccomp module disabled; changes to that module's seccomp require a normal reboot. Installation stages files only. Reboot normally to activate this package.

post-fs-data.sh checks the full kernel-notes SHA-256, decompressed config SHA-256 and four payload hashes, then makes at most one normal load attempt in that boot. service.sh never loads the KO: after Android is ready it starts one locked instance of the original author watcher. It reads the existing HMA configuration and watches package/config changes. It does not write HMA templates or rules. The author may update this module's own description in module.prop.

The module action prints native status. State and private sync logs are confined to the module's state directory. A successful install or zero helper exit code is not a detector result: inspect actual hook counts, nonzero committed pairs and APK/failure counters, then test the detector manually in a fresh process.

## Target and validation

The approved target has GNU build ID fa100a608d841472 and config SHA-256 9751e53f21287e8a75b3338eb34172dcd19692e58fc6a6c39da77c7259bb0516. Full notes and approved payload hashes are recorded in config/approved.json. A frozen uname string alone never permits loading on another kernel. Geometry is VA39/page12; module_layout is 0x894a26ae. See docs/build.md for normal build and packaging commands.

The cold-boot gate requires complete native/compat counts (4+4 with the LSM hook, or the source-defined 10+10 setter fallback), actual nonzero author rule commits and successful APK registration. Detector behavior, isolated-child coverage and long-term effects require their own runtime observations.

## Disable, update and rollback

A normal KernelSU disable/uninstall takes effect after a normal reboot. Do not hot-unload this module. Updating stages the new package for the next boot; it never replaces the resident KO or starts a second watcher during installation.

For a failed candidate, disable hma_uidfake_mix4 through the native manager/ksud, restore cq_uid_seccomp through its native enable command if desired, and reboot normally. Reboot clears the manually or automatically loaded KO. This module never silently changes the old cq switch; do not run both approaches together.

## Upstream maintenance and license

Retain and merge the agreed upstream Anatdx main history; review the 5.4 port and lifecycle changes, then repeat ABI/actual CFI and runtime gates when compiled inputs change. The pinned approved binaries may be reused only when their exact source inputs remain identical. New output hashes require new evidence before updating the approval file.

Private HMA lists/configurations, raw device receipts, credentials and generated binaries do not belong in this repository. This task does not introduce Actions, schedules, tags or Releases. LICENSE retains the upstream GPL-2.0 terms; the JSON header dependency is nlohmann/json under MIT and is fetched or supplied separately for building only.
