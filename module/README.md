# HMA UID Fake — MIX4 package

This package accepts only the full kernel-notes/config hashes in common.sh and the approved four payload hashes. package.json binds the source commit and tree.

Install through the native BakaSU manager/ksud and reboot normally. Installation stages files only. post-fs-data.sh makes at most one normal finit_module(flags=0) attempt per boot; service.sh never retries a loader and runs one locked instance of the original HMA/package watcher after Android is ready.

Use the module action for real STATUS counters. Keep cq_uid_seccomp disabled to avoid two filtering methods. HMA rules/templates are not written.

Disable, update or uninstall through the native module controls and reboot; never hot-unload. To roll back a failed candidate, disable this package, restore the old cq switch if desired, and reboot normally. The old switch is never changed automatically.

The module is GPL-2.0; LICENSE and NOTICE accompany the code/runtime dependencies. The source and normal build entry are at https://github.com/kafuuchino-s/hma-uidfake on mix4-5.4.
