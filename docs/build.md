# MIX4 normal build and package entry

Use Python 3.9+ and the repository's build.sh (or python3 tools/mix4.py). Generated objects, logs and packages must stay outside the source checkout. No kernel or private configuration is downloaded.

## Reuse the validated payloads

Supply an artifact directory with hma_uidfake.ko, load-ko, kauxctl and sync-tool. verify checks the fixed approved hashes and ELF architecture; package additionally requires a clean committed source tree and binds its commit/tree into package.json.

    ./build.sh verify --artifacts /absolute/path/to/payloads
    ./build.sh package --artifacts /absolute/path/to/payloads --out /absolute/path/to/hma_uidfake_mix4.zip

The package contains only the reviewed lifecycle scripts, the four payloads, GPL license, source mapping and payload checksums. No upstream rewriting loader, private rule list, service template or generated binary is committed.

## Build user tools with an existing NDK

The tested toolchain is Android NDK r27d (27.3.13750724), Clang 18.0.4, API33/arm64, static libc++ and dynamic Android system libraries. The JSON single-header input is nlohmann/json v3.11.3 at 9cca280a4d0ccf0c08f47a99aa71d1b0e52f8d03, SHA-256 9bea4c8066ef4a1c206b2be5a36302f8926f7fdc6087af5d20b417d0cf103ea6. Supply that existing header; the entry does not download a toolchain or dependency automatically.

    ./build.sh tools --ndk /absolute/android-ndk-r27d --json-header /absolute/nlohmann/json.hpp --out /absolute/build-tools

The helper uses the author's original 13 translation units. kauxctl links the original netlink/paging client and shared protocol header; its status mode does not write module.prop. load-ko makes only one normal finit_module call. Build concurrency is at most two. Source/header paths can change helper bytes as well; rebuilt outputs remain review candidates until their exact hashes have the required evidence.

## Build the kernel module through normal external Kbuild

Supply the matching prepared kernel tree/output, its original recipe, and AOSP Clang 11.0.2. The entry copies only generated headers/configuration and host build helpers to a separate output. It invokes only the normal external modules target, including modpost/.mod.o/.ko; it never runs the kernel's build.sh or writes the supplied kernel output.

    ./build.sh module --kernel /absolute/kernel --kernel-out /absolute/kernel/out --recipe /absolute/kernel/configs/dream-3.0.308.0/odin.json --clang-bin /clang/bin --out /absolute/build-module

The copied input config and Module.symvers must match the approved target. CFI/SCS/LTO and normal CRC/vermagic checks remain enabled. Changed debug/source paths can change the KO hash; build output is a review candidate, not automatic approval. The initial package intentionally reuses the byte-identical proven KO. If verify rejects a rebuilt hash, obtain the corresponding full ABI/actual kernel-and-module CFI/runtime evidence before changing config/approved.json.

## Validate a new maintained version

Keep the source commit, both kernel dependency pins, toolchain, config and outputs bound. Require normal imports/CRCs, no duplicate exports, the real CFI caller/target tables, the lifecycle scripts and cold-boot runtime counters. An existing approved hash must never be changed merely to silence a mismatch. No nocfi addition, CFI/SCS disable, export/CRC/vermagic alteration or rewriting-loader fallback is accepted by this entry.

The upstream docs/design.md describes the general policy design; the locked UID-presence check in src/policy.c and this branch's lifecycle scripts define the 5.4 port. In particular, native getpriority ESRCH is not an existence oracle for user_struct.
