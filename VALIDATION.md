# Recorded validation

This file records observations, not guarantees for another host. Follow
[TUTORIAL.md](TUTORIAL.md) for the lessons and its
[Chapter 16](TUTORIAL.md#chapter-16--validation-and-a-clean-checkout) for checks.

## Original reference build

Before the source baseline commit, the kernel and static ARMv5 userspace built
successfully. The root image was exactly 67,108,864 bytes. All five image
tests passed, including real ext2 creation, ownership, modes, symlinks and
replacement. The two-boot smoke test passed `WRITE-OK` and `PERSISTENCE-OK`
on a copied disk; repeating `hello-arm simple-image` reused all 27 tasks.
A separate snapshot boot wrote a file without changing the deployed image's
SHA-256.

This used Python 3.14.4, GCC 15.2.0, QEMU 10.2.1 and e2fsprogs 1.47.2.
Missing host tools were extracted into ignored `tools/host`, with local
validation-only `tools/with-host` and `tools/host.conf`. Those helpers are not
source prerequisites and are not the recommended student setup.

## Clean student reconstruction, 2026-09-30

The baseline tutorial was followed in a separate, initially empty
`try-distro-tut` directory, introducing metadata chapter by chapter. It started
without a BitBake checkout, source archives, work directories or stamps.
The user installed Chapter 2's host packages with sudo; subsequent builds
used the normal system tools, not the earlier extracted-tool wrappers.

Observed results:

| Check | Result |
| --- | --- |
| Bootstrap | Pinned BitBake 2.18.0 commit verified |
| Source archive hashes | Linux and BusyBox matched the recipe pins |
| Greeting and static ARM example | Built; ARM executable had no `INTERP` |
| Kernel | Built in about 13.7 minutes on four cores; built-ins and deployed DTB checked |
| BusyBox | Fetch/build about 2.7 minutes; static ARM output and applet links checked |
| Root image | 67,108,864 bytes; `e2fsck -fn` clean; root ownership checked |
| Manual console sequence | Four boots through the public wrapper; persistence survived; snapshot-only file disappeared |
| Image tests | 5 passed, none skipped |
| Smoke test | `WRITE-OK` and `PERSISTENCE-OK`; about 33 seconds |
| Incremental combined build | All 27 tasks reused |
| Generated tree size | About 2.3 GB |

The console reported `Power off not available: System halted instead`;
Ctrl-a x was required to exit QEMU after each `poweroff`.
The observed kernel timestamp warning remained despite 256-byte ext2 inodes.
Chapter 15's forced-task commands and the narrower DTS rebuild path were
also exercised. Recipe sources matched the reference after restoring edits.

These results apply to the original tutorial recorded by baseline commit
`01ff564`, not automatically to every subsequent enhancement.

## Scope

Neither successful boot nor static linking establishes production hardening,
license compliance, reproducible output across host toolchains or correctness
of every BusyBox applet. No physical-board testing is claimed. The optional
program exercise and revised metadata tests require their own validation.
