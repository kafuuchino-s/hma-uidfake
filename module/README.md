# HMA UID Fake — Xiaomi Pad 5 Pro / elish 4.19

Module ID `hma_uidfake_elish`, version `0.3.3-elish.1` / code `303101`.

This package targets the frozen elish 4.19.325 kernel with GNU build ID
`a98e5b4c8549e8e2` and complete kernel notes SHA-256
`f97c09b8e6c902eb05b9365dd9010493b324398effb7d6986f82a1d6cb5859d1`. Its actual source configuration SHA-256 is
`ffa1642d8ca8b3e71362a135e28bbec81c99ae307c3b1aaed86b7a29619d0d09`.
The kernel's original MIUI recipe deliberately embeds an `elish_stock-defconfig`
view; `/proc/config.gz` is expected to decompress to that view, SHA-256
`197c535c9ba32d8123f2edeba143c09afe8acf6ee8af801d2e0b91e4291fa279`.
This visible view is distinct from the real source configuration. Complete notes,
visible config view and approved payload bytes are checked before activation;
the actual source configuration is bound offline to those final kernel notes.

Install using native KernelSU/BakaSU module installation on the bound kernel.
Installation stages files; reboot normally to activate. The parent's device
baseline has no old `cq_uid_seccomp` or `hma_uidfake` module, so no old-module
switch is required. Keep conflicting UID implementations disabled.

`post-fs-data.sh` allows one normal `finit_module(..., flags=0)` attempt per boot.
The ordinary kernel loader checks the module's normal GPL resolver import and
all its CRCs. The module then resolves all 22 required core symbols before
publishing its four native, four compat and exact `cap_task_fix_setuid` hooks.
No procfs symbol addresses or lowered `kptr_restrict` are required.
The script checks the real v3 / 104-byte STATUS for native 4/4, compat 4/4 and
LSM 1; a failed load is recorded and is not retried by `service.sh`.

After Android finishes booting, `service.sh` obtains a nonblocking fd 9 flock
before it execs one author `sync-tool` process. It reads the installed HMA rules,
watches their changes and updates UID/APK policy. It is started without template
or config-writing arguments. The HMA rules, scope and templates remain the user's.
Use the KernelSU action to read the actual current STATUS and inspect `state/`
for the local load and sync receipts.

Disable or uninstall through KernelSU and reboot to end the kernel hooks. The
package does not hot-unload the module or automatically enable the old UID module.
Its kernel module still inherits upstream removal code; hot-unload concurrency
has not been accepted for this port.

The payload has offline build, ABI and source validation. Live rule counts,
APK identities, unique watcher ownership, post-reboot operation and detector
results require the parent device owner's runtime acceptance. A successful
STATUS is not an application detector result.

GPL-2.0 history and attribution are retained. The reference is
`kafuuchino-s/hma-uidfake@0ab1cc0a434cded47001e736475abec9dfb28df1`;
this local elish port is delivered with its source bundle and patch. The three
unchanged Android userspace tools are reused by exact approved bytes with their
source and ABI evidence; no MIX4 kernel module or kernel approval is reused.
