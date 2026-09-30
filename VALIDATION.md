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

## Enhanced tutorial verification, 2026-09-30

Source revision: `e958f0a` (the 14 enhancement commits after `01ff564`).
Host: Ubuntu 26.04.1 LTS, Python 3.14.4, native/cross GCC 15.2.0,
QEMU 10.2.1 and e2fsprogs 1.47.2, using normal system packages.
No extracted-host-tool wrapper was used.

Two complementary runs were performed:

1. In the reference project, `scripts/bb hello hello-arm simple-image`
   rebuilt affected tasks against the updated metadata. This reused existing
   source/work caches and is not described as a clean build.
2. An independent clone of `e958f0a` started without `tools/`, `downloads/`,
   work directories or stamps. Bootstrap fetched the pinned engine from
   upstream; a second bootstrap invocation verified it unchanged. Chapter
   14's optional exercise was applied before `scripts/bb hello simple-image`.
   All 29 scheduled tasks ran successfully, including fresh Linux and BusyBox
   downloads/builds and automatic staging of `hello-arm`.

| Verification | Observed result |
| --- | --- |
| `python3 -m unittest discover -s tests -v` | 10 passed, 0 skipped |
| Ambient host environment regression | Changing PATH/HOME/USER/LOGNAME/PWD/SHELL reused greeting tasks; editing recipe code still rebuilt them |
| Complete-image PATH regression | Adding `/tmp` to PATH reused all 27 `hello-arm simple-image` tasks in the reference project |
| Inline metadata and local documentation links | Matched source; all checked local link targets existed |
| Reconstruction checkpoints | Initial inline metadata built `hello`; fetch-only Linux parsed without build/deploy classes; replacing it added compile/devicetree tasks |
| Tutorial command syntax | All 46 shell blocks passed `sh -n` |
| Source archive hashes | Both fresh downloads matched pinned SHA-256 values |
| Default image | 67,108,864 bytes; offline `e2fsck -fn` passed |
| Revised DTB inspection command | Decoded first SD slot with `non-removable` and SIC interrupts 22/1; warnings retained in a log |
| Reference image persistence | `WRITE-OK` and `PERSISTENCE-OK` |
| Optional program in fresh image | Public QEMU wrapper booted; guest `hello-arm` printed `Hello from ARM userspace!` |
| Snapshot and shutdown | Guest wrote a disposable file, synced, powered off to a halt; Ctrl-a x exited QEMU; deployed disk SHA-256 was unchanged |
| Optional image persistence | `WRITE-OK` and `PERSISTENCE-OK` |
| Restoring default configuration | Rebuilt root tree and ext2 disk both excluded `/usr/bin/hello-arm`; persistence smoke test passed again |
| Repeated default build | All 27 tasks reused after restoration |
| Backup instructions | Sparse copy compared identical; backup path ignored by Git |
| Fresh generated tree | About 2.3 GB |

The normal persistence tests save serial transcripts under
`build/tmp/test-logs/first-boot.log` and `second-boot.log` in their respective
projects. The additional console exercise used a validation-only pexpect
driver, not a student dependency, and saved `optional-program-snapshot.log`
in the fresh clone's same log directory. Both projects were left in the
default source configuration. Generated logs and build artifacts are not
committed.

## Scope

Neither successful boot nor static linking establishes production hardening,
license compliance, reproducible output across host toolchains or correctness
of every BusyBox applet. No physical-board testing is claimed.
