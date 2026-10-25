# Local elish 4.19 port

The original upstream and MIX4 history, licenses and attribution are preserved.
The local branch `elish-4.19` starts at own reference commit
`0ab1cc0a434cded47001e736475abec9dfb28df1` (tree
`b36d23fc48664e4966f84939e2cb3aecd83c45ad`). Upstream retained source is
`Anatdx/hma-uidfake@dcc8c1993f355de083d1beca834da423c0ae2098`.

This port targets the parent-frozen 4.19.325 elish GPL-resolver kernel only:
kernel `a9bec2ab96b256ae78df8261681f1c63add6060b`, BakaSU `fdc26bf136d52cd6e2f3415e215a88096e110e08`.
SUSFS 2.3 is integrated into that kernel tree. CFI, SCS and KPROBES stay off as
in the approved original MIUI source config. Source config and the intentionally
hidden stock config view are recorded separately in `config/elish-approved.json`.

Local kernel compatibility changes:

* The explicit 4.19 elish build profile imports the kernel's ordinary
  `EXPORT_SYMBOL_GPL(kallsyms_lookup_name)` and carries its native Module.symvers
  CRC. This is a direct normal GPL import. It does not read `/proc/kallsyms`,
  lower `kptr_restrict`, change visibility settings, reconstruct a resolver,
  or require another resolver export. If needed, `kallsyms_on_each_symbol` is
  obtained by that normal lookup. Module init validates all 22 required core
  symbols before publishing any hook.
* The four native and four compat syscall slots and the actual
  `cap_task_fix_setuid` hlist slot are prepared together. Original callbacks,
  all addresses, page references and nine RW/NX vmap aliases are ready before
  `stop_machine`. The stopped callback checks all nine original/alias values
  before its first store, then publishes the nine pointers without a fallible
  operation or error return after the first store. Earlier preparation errors
  propagate through module init and free only unpublished policy/netlink state.
* The unexported 4.19 `get_task_cred` call is replaced locally with the exact
  target kernel's RCU plus `get_cred_rcu` reference loop. No new private function
  call, export or CFI exception is introduced by this local helper.
* Real locked uidhash existence, hash decoding, tag policy, the four UID APIs,
  author synchronization and the v3 STATUS ABI remain intact. The shifted-add
  hash is verified against the final linked `find_user` implementation.

The standard package is described in `module/README.md`. Its independent tablet
approval is `config/elish-approved.json`; build `tools/elish-package.py
--artifacts DIR --out DIR` only from a clean committed tree. The retained
`tools/mix4.py` and MIX4 approvals describe the historical reference and
intentionally do not build this changed port.

The normal external module build, frozen-input checks and detailed ELF/source
validation are delivered alongside the local source bundle in the tablet's
`research/root-uid-update/uid/` directory. No remote ref, workflow, tag, release,
schedule or device is changed by this port. Runtime and detector acceptance
remain separate from these offline results. Hot unload is not an accepted
operation; use a normal reboot to end the hooks.
