# Project Board — Extending the BitBake Tutorial (Group Edition)

This is the **student-facing task board** for the project described in full detail in
[tasklist.md](/home/test/git/simple-distro/bitbakers/tasklist.md). Read the goal and hard
constraints there once before you start — this board only tracks *who is doing what* and
*current status*; the design detail for each task lives in `tasklist.md`.

## 0. How this works

1. **Claim a task.** Open a PR that edits only your row(s) in the tables below: put your
   GitHub handle in **Assignee** and set **Status** to `claimed`. One task, one owner. If a
   task looks too big, split it in the PR description and claim only your slice.
2. **Check dependencies first.** The **Depends on** column lists task IDs that must be
   `merged` before you can meaningfully start. Don't start work whose dependencies are still
   `in progress` — coordinate in the task's tracking issue instead (see §2).
3. **Do the work on a branch** named `taskid-short-description`, e.g. `t17.2-busybox-recipe`.
4. **Definition of done** (from `tasklist.md` §5): every task is complete only once it has
   gone through all four steps:
   - **design** — short note in the PR description of the approach (variables/files touched)
   - **implement** — the actual class/recipe/config/script
   - **document** — the matching prose added to
     [A-Practical-Guide-to-BitBake-2026.md](/home/test/git/simple-distro/bitbakers/A-Practical-Guide-to-BitBake-2026.md)
   - **verify** — run the command in the Verification Matrix (§4 below) and paste the output
     in the PR
5. **Respect the additive rule** (see `tasklist.md` §3.1): don't touch metadata or variables
   owned by an already-merged chapter unless your task explicitly says to. If you must,
   flag it loudly in the PR and re-run `check-chapter.sh --no-rebuild` (T0.5) to prove you
   didn't force a kernel/BusyBox rebuild.
6. **Open a PR against `main`** for review by at least one other student before merging.
   Merge **in dependency order** — the phases below are numbered for a reason; Phase *N*
   should generally be merged before Phase *N+1* starts in earnest, except within Phase 0
   where tasks are independent.
7. **Update this file in the same PR** that finishes the task: flip **Status** to `merged`
   once it lands, and link the **PR #**.

Status values: `open` → `claimed` → `in review` → `merged`. Use `blocked` (with a one-line
reason in the row) if you're stuck on something outside your control.

## 1. Ground rules (condensed — see `tasklist.md` for the full versions)

* No Yocto/OE-Core/ready-made layers — only upstream BitBake plus what we write ourselves.
* Every Part II chapter snapshot (`ch11/` … `ch21/`) must stay runnable and diffable against
  the previous one.
* All Part II chapters share one `TMPDIR`/`DL_DIR` (`bitbakers/shared/`) — the kernel and
  BusyBox are each compiled exactly once for the whole tutorial. This is why the additive
  rule in §0.5 matters: an incompatible edit forces everyone's next build to recompile the
  kernel.
* No `sudo`, no loop mounts — the ext2 image is built entirely with `mke2fs -d`.
* Target versions are pinned: Linux **7.2.6**, BusyBox **1.38.0** (see T0.7 for checksums).

## 2. Coordination

* Use one GitHub Issue per **Phase** (12 issues total) as the discussion thread for that
  phase's tasks; link claimed tasks and PRs there.
* If two people want the same task, whoever opens the claiming PR first gets it — the other
  picks an unclaimed task or pairs up (list both handles in **Assignee**).
* Blocking questions or decisions that affect other tasks belong in the phase issue, not
  buried in a single task's PR thread.

## 3. Task board

### Phase 0 — Groundwork *(no dependencies between these — good first tasks)*

| Task | Description | Depends on | Assignee | Status | PR # |
|------|--------------|------------|----------|--------|------|
| T0.1 | Fix `bitbakers/README.md` vs `chapters/` vs `chNN/` mismatch | — | | open | |
| T0.2 | Add `scripts/check-chapter.sh <chNN> <targets…>` verification runner | — | | open | |
| T0.3 | Create shared build area `shared/conf/shared.inc`, `shared/downloads/`, `shared/tmp/` | — | adn-dodo | claimed | |
| T0.4 | Add `bitbakers/.gitignore` for build artifacts; confirm `git status` stays clean | — | | open | |
| T0.5 | Add `check-chapter.sh --no-rebuild` mode enforcing the additive rule | T0.2 | | open | |
| T0.6 | Document host prerequisites (toolchain, qemu, e2fsprogs ≥1.43, disk/network) | — | | open | |
| T0.7 | Pin upstream versions/checksums for Linux 7.2.6 and BusyBox 1.38.0 | — | adn-dodo | cliamed | |

### Phase 1 — Ch11: From task engine to build system

| Task | Description | Depends on | Assignee | Status | PR # |
|------|--------------|------------|----------|--------|------|
| T11.1 | Design `simple-distro/` project root seeded from `meta-tutorial` | T0.3 | | open | |
| T11.2 | Implement `meta-core/conf/bitbake.conf` additions (TMPDIR, WORKDIR, S/B/D, STAGING_DIR, DEPLOY_DIR_IMAGE, …) | T11.1 | | open | |
| T11.3 | Implement `meta-core/conf/layer.conf` | T11.1 | | open | |
| T11.4 | Write Chapter 11 prose | T11.2, T11.3 | | open | |
| T11.5 | Verify (`bitbake -e`, `bitbake-layers show-layers`); snapshot `ch11/` | T11.2, T11.3 | | open | |

### Phase 2 — Ch12: Fetching and unpacking sources

| Task | Description | Depends on | Assignee | Status | PR # |
|------|--------------|------------|----------|--------|------|
| T12.1 | Implement `meta-core/classes/fetch.bbclass` (`do_fetch`, `do_unpack`) | T11.5 | | open | |
| T12.2 | Add `do_patch` task (`patch -p1` loop over `SRC_URI` patches) | T12.1 | | open | |
| T12.3 | Throwaway demo recipe `hellosrc` | T12.1 | | open | |
| T12.4 | Document fetcher URI syntax, checksum failures, `-c cleanall` | T12.1, T12.2 | | open | |
| T12.5 | Verify unpack + stamp no-op; snapshot `ch12/` | T12.1–T12.4 | | open | |

### Phase 3 — Ch13: A real task chain

| Task | Description | Depends on | Assignee | Status | PR # |
|------|--------------|------------|----------|--------|------|
| T13.1 | Implement `meta-core/classes/build.bbclass` (`do_configure`/`do_compile`/`do_install`) | T12.5 | | open | |
| T13.2 | Document task flags: `nostamp`, `noexec`, `dirs`, `cleandirs`, `depends`, log locations | T13.1 | | open | |
| T13.3 | Write "Stamps, signatures and the shared build" section (`basichash`, `BB_BASEHASH_IGNORE_VARS`, `bitbake-diffsigs`) | T13.1 | | open | |
| T13.4 | Demo recipe: host-compiled C program installed to `${D}${bindir}` | T13.1 | | open | |
| T13.5 | Document clean/rebuild workflow (`-c clean`, `-c cleanall`, `-f -c compile`, `-C`) | T13.1 | | open | |
| T13.6 | Verify binary + rebuild-on-edit proof; snapshot `ch13/` | T13.1–T13.5 | | open | |

### Phase 4 — Ch14: Cross compilation

| Task | Description | Depends on | Assignee | Status | PR # |
|------|--------------|------------|----------|--------|------|
| T14.1 | Add toolchain variables (`TARGET_ARCH`, `TARGET_PREFIX`, `CROSS_COMPILE`, `CC`/`LD`/`AR`, …) | T13.6 | | open | |
| T14.2 | Add sanity check (`bb.fatal` if `${TARGET_PREFIX}gcc` missing) | T14.1 | | open | |
| T14.3 | Document `BB_ENV_PASSTHROUGH_ADDITIONS` and clean-environment `PATH` handling | T14.1 | | open | |
| T14.4 | Verify ARM EABI5 binary; snapshot `ch14/` | T14.1–T14.3 | | open | |

### Phase 5 — Ch15: Machines and distros

| Task | Description | Depends on | Assignee | Status | PR # |
|------|--------------|------------|----------|--------|------|
| T15.1 | Implement `meta-core/conf/machine/versatilepb.conf` | T14.4 | | open | |
| T15.2 | Implement `meta-core/conf/distro/simple.conf` | T14.4 | | open | |
| T15.3 | Document `OVERRIDES` in practice (`:append:versatilepb`, etc.) | T15.1, T15.2 | | open | |
| T15.4 | Verify `MACHINE` change propagates via `bitbake -e`; snapshot `ch15/` | T15.1–T15.3 | | open | |

### Phase 6 — Ch16: Dependencies and the sysroot

| Task | Description | Depends on | Assignee | Status | PR # |
|------|--------------|------------|----------|--------|------|
| T16.1 | Implement `meta-core/classes/staging.bbclass` (`do_populate_sysroot`, `deptask`) | T15.4 | | open | |
| T16.2 | Document `DEPENDS` vs `deptask`, and `do_task[depends]` | T16.1 | | open | |
| T16.3 | Demo recipes `libdemo` → `appdemo`; `bitbake -g` / dot graph | T16.1 | | open | |
| T16.4 | Verify ordering (`libdemo:do_populate_sysroot` before `appdemo`); snapshot `ch16/` | T16.1–T16.3 | | open | |

### Phase 7 — Ch17: BusyBox

| Task | Description | Depends on | Assignee | Status | PR # |
|------|--------------|------------|----------|--------|------|
| T17.1 | Create `meta-distro` layer | T16.4 | | open | |
| T17.2 | Write `recipes-core/busybox/busybox_1.38.0.bb` | T17.1, T0.7 | | open | |
| T17.3 | Config fragment for init/ash/mount applets needed for ext2 boot | T17.2 | | open | |
| T17.4 | Document why static BusyBox removes the need for a libc recipe | T17.2 | | open | |
| T17.5 | Verify static ARM `busybox` + `sbin/init` symlink, no-op rebuild; snapshot `ch17/` | T17.1–T17.4 | | open | |

### Phase 8 — Ch18: Kernel

| Task | Description | Depends on | Assignee | Status | PR # |
|------|--------------|------------|----------|--------|------|
| T18.1 | Create `meta-bsp` layer + `recipes-kernel/linux/linux_7.2.6.bb` | T17.5, T0.7 | | open | |
| T18.2 | Implement `meta-core/classes/kernel.bbclass` | T18.1 | | open | |
| T18.3 | Add `KERNEL_CONFIG_FRAGMENTS` support + `versatilepb-extra.cfg` (devtmpfs, no initrd) | T18.2 | | open | |
| T18.4 | Implement `meta-core/classes/deploy.bbclass` + kernel `do_deploy` | T18.2 | | open | |
| T18.5 | Document long-build ergonomics (`PARALLEL_MAKE`, `-c compile -f`, manual config inspection) | T18.2–T18.4 | | open | |
| T18.6 | Verify zImage+dtb deploy, QEMU reaches "Unable to mount root fs"; snapshot `ch18/` | T18.1–T18.5 | | open | |

### Phase 9 — Ch19: base-files, init and `/etc`

| Task | Description | Depends on | Assignee | Status | PR # |
|------|--------------|------------|----------|--------|------|
| T19.1 | Write `recipes-core/base-files/base-files_1.0.bb` + FHS skeleton `do_install` | T18.6 | | open | |
| T19.2 | Ship `inittab`, `rcS`, `fstab`, `profile` for a real (non-initramfs) root | T19.1 | | open | |
| T19.3 | Document the init contract (`/init` vs `/sbin/init`, `rdinit=`, `init=/bin/sh`) | T19.1, T19.2 | | open | |
| T19.4 | Verify staged tree + permissions, confirm kernel **not** rebuilt (additive rule); snapshot `ch19/` | T19.1–T19.3 | | open | |

### Phase 10 — Ch20: The ext2 image

| Task | Description | Depends on | Assignee | Status | PR # |
|------|--------------|------------|----------|--------|------|
| T20.1 | Implement `meta-core/classes/image.bbclass` (`do_rootfs`, `do_image`, `IMAGE_CMD:ext2`) | T19.4 | | open | |
| T20.2 | Write `recipes-core/images/simple-image.bb` | T20.1 | | open | |
| T20.3 | Document ext2 gotchas (sizing, `mke2fs` version, ownership, devtmpfs dependency) | T20.1, T20.2 | | open | |
| T20.4 | Document the deliberate no-package-manager simplification | T20.1 | | open | |
| T20.5 | Verify `rootfs.ext2` deploy + `debugfs`/`dumpe2fs` inspection, kernel **not** rebuilt; snapshot `ch20/` | T20.1–T20.4 | | open | |

### Phase 11 — Ch21: Booting, debugging, iterating

| Task | Description | Depends on | Assignee | Status | PR # |
|------|--------------|------------|----------|--------|------|
| T21.1 | Add `recipes-core/qemu/runqemu_1.0.bb` (`addtask run`, standalone `runqemu.sh`) | T20.5 | | open | |
| T21.2 | Document expected boot transcript + persistence demo (write file, reboot, still there) | T21.1 | | open | |
| T21.3 | Write ext2-first troubleshooting section | T21.1 | | open | |
| T21.4 | Write debugging toolbox recap (`-e`, `-g`, `-DDD`, `-c listtasks`, `debugfs`) | T21.1 | | open | |
| T21.5 | Verify end-to-end on a clean checkout (`bitbake simple-image && bitbake -c run runqemu`); snapshot `ch21/` | T21.1–T21.4 | | open | |

### Phase 12 — Wrap-up and exercises

| Task | Description | Depends on | Assignee | Status | PR # |
|------|--------------|------------|----------|--------|------|
| T22.1 | Rewrite Chapter 10 "Summary" as Chapter 22 (what was built, what Yocto adds) | T21.5 | | open | |
| T22.2 | Add graded exercises (cpio.gz image type, SCSI root, ext4 type, `.bbappend` fragment, second image recipe) | T21.5 | | open | |
| T22.3 | Update `bitbakers/README.md` chapter list and usage instructions | T22.1 | | open | |
| T22.4 | Cross-link `README.simple-linux-distro` ↔ tutorial, state intentional differences | T22.1 | | open | |

## 4. Verification matrix (for reviewers)

Reproduced from `tasklist.md` §6 — a PR for a chapter's tasks should paste the output of its
row before requesting review.

| Chapter | Command run from `chNN/build` | Must produce |
|---------|-------------------------------|--------------|
| 11 | `bitbake -e` | new variables expand, no parse errors |
| 12 | `bitbake -c unpack hellosrc` | unpacked tree in `tmp/work` |
| 13 | `bitbake hellodemo` | host binary in recipe image dir |
| 14 | `bitbake hellodemo` | ARM EABI5 binary |
| 15 | `bitbake -e \| grep KERNEL_DEFCONFIG` | machine value present |
| 16 | `bitbake appdemo` | ordered tasks, dot graph |
| 17 | `bitbake busybox` | static ARM `busybox` + `sbin/init` link |
| 18 | `bitbake linux` | `zImage` + dtb deployed, `CONFIG_DEVTMPFS_MOUNT=y`, QEMU reaches "Unable to mount root fs" |
| 19 | `bitbake base-files` | rootfs skeleton + `inittab`/`rcS`/`fstab`; kernel **not** rebuilt |
| 20 | `bitbake simple-image` | `rootfs.ext2` deployed; `debugfs -R "ls /"` lists it; kernel **not** rebuilt |
| 21 | `bitbake -c run runqemu` | interactive BusyBox shell; guest writes survive a reboot |

## 5. Publishing checklist (Phase 13 — after Phase 12 merges)

Once all tasks above are `merged`, before making the repository public:

* [ ] Pick and add a LICENSE file (not decided yet — discuss in the wrap-up issue).
* [ ] Squash/clean up chapter snapshot history if desired (optional — diffability across
  `chNN/` folders matters more than commit history).
* [ ] Do one full clean-checkout run of the Chapter 21 command (`bitbake simple-image &&
  bitbake -c run runqemu`) on a machine that never built the project before.
* [ ] Proofread the merged `A-Practical-Guide-to-BitBake-2026.md` end to end for consistent
  terminology between chapters written by different people.
* [ ] Tag a release (e.g. `v1.0-part-ii`) once the above pass.
