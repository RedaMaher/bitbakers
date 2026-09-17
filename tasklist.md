# Task List — Extending the BitBake Tutorial to Build a Simple Linux Distro

## 1. Goal

Extend [A-Practical-Guide-to-BitBake-2026.md](/home/test/git/simple-distro/bitbakers/A-Practical-Guide-to-BitBake-2026.md)
(currently Chapters 1–10, BitBake used as a pure task engine) so that, step by step, the
student ends up with a **from-scratch BitBake build system** that produces the distro
described in [README.simple-linux-distro](/home/test/git/simple-distro/README.simple-linux-distro):

* Linux kernel **7.2.6** (`zImage` + `versatile-pb.dtb`) cross-compiled for ARM
* BusyBox **1.38.0** (static) providing userspace
* A **writable ext2 root filesystem image** (`rootfs.ext2`), attached to QEMU as a virtual
  SD card and mounted by the kernel as `/dev/mmcblk0` — *not* an initramfs
* Booting under `qemu-system-arm -M versatilepb` into a BusyBox shell

Everything is produced by `bitbake simple-image` and run by one command.

Deviations from `README.simple-linux-distro` (deliberate, must be documented):

| README (manual) | Tutorial Part II | Why |
|---|---|---|
| kernel 6.7.6, BusyBox 1.36.1 | kernel 7.2.6 (stable), BusyBox 1.38.0 | current upstream releases |
| `rootfs.cpio.gz` initramfs + `/init` | `rootfs.ext2` block device + `/sbin/init` | real root filesystem, persistent writes, teaches image types and `IMAGE_CMD` |
| `-initrd rootfs.cpio.gz` | `-drive file=rootfs.ext2,if=sd,format=raw`, `root=/dev/mmcblk0 rootwait rw` | boots like a real board |

## 2. Hard constraints

* **No Yocto, no OE-Core, no ready-made layers.** Only upstream BitBake 2.18 plus the
  minimal `base.bbclass` / `bitbake.conf` already copied in Chapter 4.
* Every class (`fetch`, `staging`, `image`, …) is written by the student, incrementally.
* Each new chapter keeps the existing style: short prose → exact file contents → command
  to run → expected output.
* Each chapter gets its own snapshot directory `bitbakers/chNN/`, like `ch04`…`ch09` —
  but Part II chapters share **one** build output directory, so the kernel is compiled once
  for the whole tutorial (see §3.1).
* **Incremental and explanatory over fast**: Chapters 12–16 introduce each mechanism with a
  small throwaway demo recipe, so a concept is never learned at the same time as a 30-minute
  kernel build. BusyBox and the kernel arrive only once the mechanism is already understood.
* Host prerequisites stay the ones from the README plus image tooling:
  `gcc-arm-linux-gnueabi`, `qemu-system-arm`, kernel build deps, and
  **`e2fsprogs >= 1.43`** (for `mke2fs -d`, verified here as 1.47.2). The cross toolchain is
  **used**, not built (out of scope — see §7).
* **No `sudo`, no loop mounts.** The ext2 image is built entirely in user space with
  `mke2fs -d <rootfs-dir>`; students never need root to create a filesystem image.

## 3. Target architecture (end state, Chapter 21)

```
simple-distro/                      # new project root, created in Ch11
├── build/
│   └── conf/
│       ├── bblayers.conf
│       └── local.conf              # MACHINE, DISTRO, PARALLEL_MAKE, DL_DIR
├── meta-core/                      # the "build system" layer
│   ├── classes/
│   │   ├── base.bbclass            # extended tutorial base
│   │   ├── fetch.bbclass           # do_fetch / do_unpack / do_patch
│   │   ├── build.bbclass           # do_configure / do_compile / do_install chain
│   │   ├── staging.bbclass         # do_populate_sysroot + deptask wiring
│   │   ├── deploy.bbclass          # do_deploy into DEPLOY_DIR_IMAGE
│   │   ├── kernel.bbclass          # shared kernel make logic + config fragments
│   │   └── image.bbclass           # rootfs assembly + ext2 image creation
│   └── conf/
│       ├── bitbake.conf            # extended: SYSROOT, IMAGE_*, TARGET_*
│       ├── layer.conf
│       ├── distro/simple.conf
│       └── machine/versatilepb.conf
├── meta-bsp/                       # board/kernel layer
│   └── recipes-kernel/linux/
│       ├── linux_7.2.6.bb
│       └── files/versatilepb-extra.cfg   # DEVTMPFS, DEVTMPFS_MOUNT, EXT2 rw
└── meta-distro/                    # userspace + image layer
    ├── recipes-core/busybox/busybox_1.38.0.bb (+ files/static.cfg)
    ├── recipes-core/base-files/base-files_1.0.bb
    │       └── files/{inittab,rcS,fstab,profile}
    ├── recipes-core/images/simple-image.bb
    └── recipes-core/qemu/runqemu_1.0.bb   # runnable "boot it" task
```

Three layers are deliberate: they let the tutorial reuse Chapter 7 (layers), Chapter 8
(`.bbappend`, `require`/`include`) and Chapter 9 (variables) knowledge in a realistic split
of *build system* vs *BSP* vs *product*.

### 3.1 Repository layout: per-chapter metadata, one shared build

Chapter snapshots stay consistent with `ch04`…`ch09` (each `chNN/` is a complete, runnable
project you can diff against `ch(NN-1)/`), but **all Part II chapters write their output to
one shared `TMPDIR` and `DL_DIR`**, so the kernel tarball is downloaded once and the kernel
is compiled once for Chapters 18–21 instead of four times.

```
bitbakers/
├── ch04 … ch09/                    # unchanged, self-contained (Part I)
├── ch11 … ch21/                    # Part II snapshots — metadata only, no tmp/
│   ├── build/conf/{bblayers.conf,local.conf}
│   ├── meta-core/  meta-bsp/  meta-distro/
├── shared/
│   ├── conf/shared.inc             # TMPDIR, DL_DIR, parallelism, hash settings
│   ├── downloads/                  # DL_DIR          (git-ignored)
│   └── tmp/                        # TMPDIR          (git-ignored)
├── scripts/check-chapter.sh
└── .gitignore
```

Every Part II `build/local.conf` starts with one line:

    require ${TOPDIR}/../../shared/conf/shared.inc

and `shared/conf/shared.inc` contains:

    BBGUIDE_SHARED := "${@os.path.normpath(d.getVar('TOPDIR') + '/../../shared')}"
    DL_DIR  = "${BBGUIDE_SHARED}/downloads"
    TMPDIR  = "${BBGUIDE_SHARED}/tmp"
    BB_NUMBER_THREADS ?= "4"
    PARALLEL_MAKE     ?= "-j 8"
    BB_SIGNATURE_HANDLER = "basichash"
    BB_BASEHASH_IGNORE_VARS += "TMPDIR DL_DIR TOPDIR FILE FILE_DIRNAME THISDIR \
                                LAYERDIR BBPATH PATH PWD DATE TIME \
                                BB_NUMBER_THREADS PARALLEL_MAKE BB_TASKHASH"

This works because `bitbake.conf` ends with `require local.conf` (added in Chapter 8), so the
shared values override the defaults.

**Why the hash settings are not optional.** Plain BitBake defaults to the `noop` signature
handler, where a stamp file alone marks a task done — edit a recipe and nothing rebuilds.
`basichash` makes stamps depend on the metadata, which is both correct *and* what lets
chapters share a `TMPDIR`: Chapter 19's kernel task hash is identical to Chapter 18's, so the
stamp is still valid and the kernel is not rebuilt. `BB_BASEHASH_IGNORE_VARS` is what makes
the hash **location-independent** — without it, every chapter lives at a different path, so
`FILE`, `LAYERDIR` and `TOPDIR` would change the hash and force a full kernel rebuild per
chapter. This is worth a dedicated section in Chapter 13.

**Consequence — the additive rule.** Part II chapters may only *add* metadata, or change
metadata belonging to recipes that chapter introduces. Anything that alters a variable an
already-built recipe consumes (e.g. touching `TARGET_CFLAGS` in Chapter 20) silently costs a
full kernel rebuild. Each chapter's review checklist must confirm this with
`bitbake -S none linux` / `bitbake-diffsigs`.

## 4. Chapter roadmap

| Ch | Title | New BitBake concept | Milestone / proof |
|----|-------|---------------------|-------------------|
| 11 | From task engine to build system | project bootstrap, extended `bitbake.conf`, `TMPDIR`/`WORKDIR`/`DEPLOY_DIR` | `bitbake -e` shows the new variables |
| 12 | Fetching and unpacking sources | `SRC_URI`, `bb.fetch2`, `DL_DIR`, checksums, `S`/`B` | tarball downloaded + unpacked by a recipe |
| 13 | A real task chain | `do_configure/compile/install`, task flags `dirs`, `cleandirs`, `nostamp`, `noexec`, stamps + `basichash` signatures, `-c clean*` | native "hello" recipe builds; editing it reruns only the right task |
| 14 | Cross compilation | `TARGET_ARCH`, `CROSS_COMPILE`, `export`, anonymous Python sanity check | same recipe produces an ARM binary (`file` output) |
| 15 | Machines and distros | `conf/machine`, `conf/distro`, `MACHINE`, `OVERRIDES`, `require` | `MACHINE=versatilepb` selects kernel/qemu settings |
| 16 | Dependencies and the sysroot | `DEPENDS`, `do_populate_sysroot`, `do_configure[deptask]`, `STAGING_DIR` | recipe B builds only after A staged its output |
| 17 | The BusyBox recipe | config fragments via `file://`, `FILESPATH`, `PARALLEL_MAKE` | static ARM BusyBox in the recipe image dir |
| 18 | The kernel recipe | `do_deploy`, `DEPLOY_DIR_IMAGE`, out-of-tree `O=` builds, defconfig + `.cfg` fragment merging | `zImage` + `versatile-pb.dtb` deployed; QEMU reaches "unable to mount root fs" |
| 19 | base-files, init and `/etc` | installing plain files, permissions, boot-time config | `/sbin/init` (BusyBox), `/etc/inittab`, `rcS`, `fstab` staged |
| 20 | The image recipe (ext2) | `IMAGE_INSTALL`, image-level `deptask`, `IMAGE_FSTYPES`, `IMAGE_CMD:<type>`, `IMAGE_ROOTFS_SIZE` | `bitbake simple-image` → `rootfs.ext2` built with `mke2fs -d`, no root |
| 21 | Booting and iterating | runnable task (`addtask run`, `nostamp`), rebuild/clean workflow, `bitbake -g`, `-e`, `-DDD` debugging | QEMU boots from the ext2 SD card to a BusyBox shell; writes persist |
| 22 | Summary & where Yocto goes further | sstate, packaging, recipes for the toolchain, QA — what we deliberately skipped | doc-only |

## 5. Task list

Legend: `[ ]` todo. Each chapter is done only when **all four** of its sub-tasks
(design → implement → document → verify) pass.

### Phase 0 — Groundwork

* [ ] **T0.1** Fix the README/chapters mismatch: `bitbakers/README.md` says examples live in
  `chapters/`, but they are at `bitbakers/ch04…ch09`. Pick one layout and make both agree.
* [ ] **T0.2** Add `bitbakers/scripts/check-chapter.sh <chNN> <targets…>` that sources
  `bbenv.include`, enters `chNN/build`, runs the chapter's commands, and fails loudly.
  Used to verify every later chapter.
* [ ] **T0.3** Create the shared build area: `shared/conf/shared.inc` (contents in §3.1),
  plus empty `shared/downloads/` and `shared/tmp/`. Every Part II `local.conf` requires it.
  Document the escape hatch for students with a small `$HOME`: override `BBGUIDE_SHARED`
  (or point `shared/` at another disk with a symlink).
* [ ] **T0.4** Add `bitbakers/.gitignore` for build artifacts:

      shared/tmp/
      shared/downloads/
      ch*/build/tmp/
      ch*/build/cache/
      ch*/build/bitbake-cookerdaemon.log
      ch*/build/*.lock
      *.ext2
      *.cpio.gz

  (The working tree is not a git repo yet — `git init` is part of this task, or the file is
  simply staged for when it becomes one.) Confirm `git status` stays clean after a full build.
* [ ] **T0.5** Teach and enforce the **additive rule** from §3.1: extend
  `check-chapter.sh` with a `--no-rebuild` mode that records
  `bitbake -S none <target>` signatures before/after and fails if a chapter invalidates the
  kernel or BusyBox task hashes. Run it for ch19, ch20 and ch21 so a stale `zImage` rebuild
  can never sneak into the tutorial.
* [ ] **T0.6** Document host prerequisites once (cross gcc, `qemu-system-arm`, kernel build
  deps, `e2fsprogs >= 1.43` for `mke2fs -d`, ~20 GB disk, network for downloads) in a new
  "Part II prerequisites" section before Chapter 11. Include the one-line check
  `mke2fs -V` and a note that no `sudo` is needed anywhere in Part II.
* [ ] **T0.7** Pin the upstream versions and checksums used by all recipes:
  * Linux **7.2.6** (stable, 2026-09-14) —
    `https://cdn.kernel.org/pub/linux/kernel/v7.x/linux-7.2.6.tar.xz`
    `sha256 039aef84f2b0994aeda3f4fcfc3d02ec9d7a9bbb9020ea264c43f446c860f606`
  * BusyBox **1.38.0** (2026-05-13) —
    `https://busybox.net/downloads/busybox-1.38.0.tar.bz2`
    `sha256 34f9ea6ff8636f2c9241153b9114eefa9e65674a45318ae1ef95bb5f31c53bb2`
  * Add a short "how to bump versions" box: rename the recipe to the new `PV`, update
    `SRC_URI[sha256sum]`, and let the `v${major}.x` path come from inline Python
    (`${@d.getVar('PV').split('.')[0]}`). Mention 6.18.x LTS as the conservative alternative.

### Phase 1 — Turn the tutorial project into a build system

* [ ] **T11.1** Design: new project root `simple-distro/` with `meta-core` seeded from
  `meta-tutorial` (`base.bbclass` + `bitbake.conf`), plus `build/conf/{bblayers,local}.conf`,
  where `local.conf` requires `shared/conf/shared.inc` (§3.1) so this and every later
  chapter build into the shared `TMPDIR`/`DL_DIR`.
* [ ] **T11.2** Implement `meta-core/conf/bitbake.conf` additions: `DISTRO`, `MACHINE`,
  `TMPDIR`, `WORKDIR`, `S`, `B`, `D` (recipe image dir), `STAGING_DIR`, `DEPLOY_DIR_IMAGE`,
  `DL_DIR`, `BB_NUMBER_THREADS`, `PARALLEL_MAKE`, `require conf/distro/${DISTRO}.conf`,
  `require conf/machine/${MACHINE}.conf`, `include local.conf`.
* [ ] **T11.3** Implement `meta-core/conf/layer.conf` with collection name, priority,
  `LAYERSERIES_COMPAT`, and `BBFILES` covering `recipes-*/*/*.bb` + `*.bbappend`.
* [ ] **T11.4** Write Chapter 11 text: why a build system is just "config + recipes + tasks"
  that we already know, and a map of what the next 10 chapters add.
* [ ] **T11.5** Verify: `bitbake -e | grep -E '^(TMPDIR|STAGING_DIR|DEPLOY_DIR_IMAGE)='`
  and `bitbake-layers show-layers`. Snapshot as `ch11/`.

### Phase 2 — Sources: fetch, unpack, patch

* [ ] **T12.1** Implement `meta-core/classes/fetch.bbclass`:
  `python do_fetch` using `bb.fetch2.Fetch(src_uri, d).download()`, `python do_unpack`
  using `.unpack(d.getVar('WORKDIR'))`, `addtask` ordering `fetch → unpack → patch → build`,
  `do_fetch[network] = "1"`, `do_unpack[cleandirs] = "${S}"`.
* [ ] **T12.2** Add a `do_patch` shell task applying `*.patch` entries from `SRC_URI`
  (keep it simple: `patch -p1` loop), demonstrating `FILESPATH` for `file://` entries.
* [ ] **T12.3** Write a throwaway demo recipe (`recipes-demo/hellosrc`) that fetches a small
  tarball, to teach `SRC_URI[sha256sum]`, `DL_DIR`, `S`, and re-fetch behaviour.
* [ ] **T12.4** Document: fetcher URI syntax (`https://`, `file://`, `git://`), checksum
  failure output, and what `-c cleanall` removes.
* [ ] **T12.5** Verify: source tree appears under `tmp/work/<pkg>/…`, second run is a no-op
  because of stamps. Snapshot as `ch12/`.

### Phase 3 — A real build chain

* [ ] **T13.1** Implement `meta-core/classes/build.bbclass`: `do_configure`, `do_compile`,
  `do_install` with `EXPORT_FUNCTIONS`, correct `addtask … after … before …` chain ending
  in `do_build`, plus `[dirs]`/`[cleandirs]` flags for `${B}` and `${D}`.
* [ ] **T13.2** Teach task flags explicitly: `nostamp`, `noexec`, `dirs`, `cleandirs`,
  `depends`, and where logs land (`temp/log.do_*`, `run.do_*`).
* [ ] **T13.3** Add a dedicated section **"Stamps, signatures and the shared build"**:
  `BB_SIGNATURE_HANDLER = "noop"` (the default — edit a recipe, nothing rebuilds) vs
  `"basichash"`, then `BB_BASEHASH_IGNORE_VARS` for location independence, and the tools
  `bitbake -S none <target>` and `bitbake-diffsigs` to answer "why did this rerun?".
  Point back to §3.1: this is exactly what lets every chapter reuse one `TMPDIR`.
* [ ] **T13.4** Demo recipe: tiny C program built with the **host** compiler, installed into
  `${D}${bindir}`.
* [ ] **T13.5** Document clean/rebuild workflow: `-c clean`, `-c cleanall`, `-f -c compile`,
  forcing with `-C`.
* [ ] **T13.6** Verify: binary exists in `tmp/work/.../image/usr/bin`; editing the recipe's
  `do_compile` makes exactly that task rerun (proof `basichash` works). Snapshot as `ch13/`.

### Phase 4 — Cross compilation

* [ ] **T14.1** Add toolchain variables to `bitbake.conf` / distro conf: `TARGET_ARCH`,
  `TARGET_PREFIX = "arm-linux-gnueabi-"`, `CROSS_COMPILE`, `CC`, `LD`, `AR`, `TARGET_CFLAGS`,
  and `export` them so shell tasks inherit them.
* [ ] **T14.2** Add an anonymous Python block (or `do_configure` guard) that fails with a
  clear `bb.fatal` if `${TARGET_PREFIX}gcc` is not on `PATH` — teaches early sanity checks.
* [ ] **T14.3** Explain `BB_ENV_PASSTHROUGH_ADDITIONS` / the clean environment BitBake uses,
  and why `PATH` handling matters.
* [ ] **T14.4** Verify: `file` on the demo binary reports `ARM, EABI5`. Snapshot as `ch14/`.

### Phase 5 — Machine and distro configuration

* [ ] **T15.1** Implement `meta-core/conf/machine/versatilepb.conf`: `MACHINE_ARCH`,
  `KERNEL_DEFCONFIG = "versatile_defconfig"`, `KERNEL_IMAGETYPE = "zImage"`,
  `KERNEL_DEVICETREE = "arm/versatile-pb.dtb"`, `KERNEL_CONFIG_FRAGMENTS`,
  `QEMU_MACHINE = "versatilepb"`, `QEMU_MEM = "128"`,
  `ROOT_DEVICE = "/dev/mmcblk0"` (virtual SD card),
  `QEMU_APPEND = "root=${ROOT_DEVICE} rootwait rw console=ttyAMA0"`.
* [ ] **T15.2** Implement `meta-core/conf/distro/simple.conf`: `DISTRO_NAME`, `DISTRO_VERSION`,
  toolchain selection, `IMAGE_FSTYPES = "ext2"`, `IMAGE_ROOTFS_SIZE = "65536"` (KiB, a power
  of two so QEMU accepts it as an SD card), default `IMAGE_INSTALL`.
* [ ] **T15.3** Teach `OVERRIDES` in practice: a variable overridden with
  `SRC_URI:append:versatilepb` or `KERNEL_EXTRA_ARGS:versatilepb`, and show it with
  `bitbake -e`.
* [ ] **T15.4** Verify: changing `MACHINE` in `local.conf` changes expanded values.
  Snapshot as `ch15/`.

### Phase 6 — Dependencies and sysroot

* [ ] **T16.1** Implement `meta-core/classes/staging.bbclass`: `do_populate_sysroot`
  copying `${D}` into `${STAGING_DIR}/${MACHINE}`, and `do_configure[deptask] =
  "do_populate_sysroot"`.
* [ ] **T16.2** Explain the key difference from the task-engine chapters: plain BitBake does
  **not** turn `DEPENDS` into task dependencies by itself — the `deptask` flag does. Also
  cover `do_task[depends] = "recipe:do_task"` for one-off cross-recipe links.
* [ ] **T16.3** Two demo recipes (`libdemo` → `appdemo`) proving ordering, then
  `bitbake -g appdemo` / `task-depends.dot` inspection.
* [ ] **T16.4** Verify: building `appdemo` alone triggers `libdemo:do_populate_sysroot`
  first. Snapshot as `ch16/`.

### Phase 7 — BusyBox

* [ ] **T17.1** Create `meta-distro` layer (`layer.conf`, `LAYERDEPENDS` on core).
* [ ] **T17.2** Write `recipes-core/busybox/busybox_1.38.0.bb`:
  `SRC_URI` = `https://busybox.net/downloads/busybox-${PV}.tar.bz2` + `file://static.cfg`,
  `SRC_URI[sha256sum] = "34f9ea6f…3bb2"`, `do_configure` = `make defconfig` then merge the
  fragment (`cat static.cfg >> .config; make oldconfig`) to get `CONFIG_STATIC=y`,
  `do_compile` with `ARCH`/`CROSS_COMPILE`/`${PARALLEL_MAKE}`,
  `do_install` = `make CONFIG_PREFIX=${D} install`.
* [ ] **T17.3** The fragment must also keep the applets the ext2 boot needs:
  `CONFIG_INIT=y` (so `/sbin/init` is a BusyBox applet), `CONFIG_FEATURE_USE_INITTAB=y`,
  `CONFIG_MOUNT`, `CONFIG_SWITCH_ROOT` off, `CONFIG_ASH=y`. Explain that with an ext2 root
  the kernel runs `/sbin/init`, not `/init` — a real init, not a shell script.
* [ ] **T17.4** Document why a static BusyBox removes the need for a libc recipe (and what
  Yocto would do instead) — keeps the tutorial honest about scope.
* [ ] **T17.5** Verify: `${D}/bin/busybox` is a static ARM binary and `${D}/sbin/init` is a
  symlink to it; `bitbake busybox` twice is a no-op. Snapshot as `ch17/`.

### Phase 8 — Kernel

* [ ] **T18.1** Create `meta-bsp` layer + `recipes-kernel/linux/linux_7.2.6.bb`
  (`SRC_URI = "https://cdn.kernel.org/pub/linux/kernel/v${@d.getVar('PV').split('.')[0]}.x/linux-${PV}.tar.xz"`,
  `sha256 039aef84…f606`).
* [ ] **T18.2** Implement `meta-core/classes/kernel.bbclass`: shared `KERNEL_MAKE_ARGS`
  (`O=${B} ARCH=${ARCH} CROSS_COMPILE=${CROSS_COMPILE}`), `do_configure` from
  `${KERNEL_DEFCONFIG}`, `do_compile` (image + dtbs + modules),
  `do_install` (`modules_install INSTALL_MOD_PATH=${D}`).
* [ ] **T18.3** Add config-fragment support to `kernel.bbclass` (`KERNEL_CONFIG_FRAGMENTS`:
  append each `.cfg` to `${B}/.config`, then `make olddefconfig`) and ship
  `meta-bsp/recipes-kernel/linux/files/versatilepb-extra.cfg`. **This is mandatory for the
  ext2 boot**, because `versatile_defconfig` in 7.2.6 has `CONFIG_EXT2_FS=y` and
  `CONFIG_MMC_ARMMMCI=y` but **no devtmpfs**:

      CONFIG_DEVTMPFS=y
      CONFIG_DEVTMPFS_MOUNT=y
      CONFIG_BLK_DEV_INITRD=n     # we no longer need an initramfs
      CONFIG_MMC_BLOCK=y

  Document *why*: the image is created by an unprivileged `mke2fs -d`, which cannot create
  `/dev/console`, so the kernel must populate `/dev` itself via devtmpfs.
* [ ] **T18.4** Implement `meta-core/classes/deploy.bbclass` and a kernel `do_deploy` that
  copies `${KERNEL_IMAGETYPE}` and `${KERNEL_DEVICETREE}` to `${DEPLOY_DIR_IMAGE}`;
  wire `addtask deploy after do_compile before do_build`. Note the 6.5+ dtb path
  `arch/arm/boot/dts/arm/versatile-pb.dtb` (verified present in 7.2.6).
* [ ] **T18.5** Teach long-build ergonomics: `PARALLEL_MAKE`, `BB_NUMBER_THREADS`,
  progress/log reading, `bitbake -c compile -f linux`, and `bitbake -c menuconfig`-style
  manual config inspection.
* [ ] **T18.6** Verify: `qemu-system-arm -M versatilepb -m 128 -kernel …/zImage
  -dtb …/versatile-pb.dtb -serial stdio -append "console=ttyAMA0"` reaches
  `VFS: Unable to mount root fs` — proof the kernel boots and is waiting for our ext2 disk.
  Also confirm `zcat …/config` (or `${B}/.config`) shows `CONFIG_DEVTMPFS_MOUNT=y`.
  Snapshot as `ch18/`.

### Phase 9 — base-files, init and `/etc`

* [ ] **T19.1** Write `recipes-core/base-files/base-files_1.0.bb` with
  `SRC_URI = "file://inittab file://rcS file://fstab file://profile"` and a `do_install`
  that creates the FHS skeleton (`bin sbin etc etc/init.d proc sys dev tmp var/log root
  usr/bin usr/sbin lib`) and installs each file with explicit modes.
* [ ] **T19.2** Ship the boot configuration for a **real root filesystem** (replacing the
  README's initramfs `/init`):
  * `/etc/inittab` — `::sysinit:/etc/init.d/rcS`, `::respawn:-/bin/sh`,
    `ttyAMA0::respawn:/sbin/getty -L ttyAMA0 115200 vt100`, `::ctrlaltdel:/sbin/reboot`
  * `/etc/init.d/rcS` (0755) — `mount -t proc none /proc`, `mount -t sysfs none /sys`,
    `mount -a`, remount `/` rw, welcome banner
  * `/etc/fstab` — `proc`, `sysfs`, `devtmpfs`, and `/dev/mmcblk0 / ext2 defaults`
  * `/etc/profile` — `PS1`, `PATH`
* [ ] **T19.3** Explain the init contract: with an initramfs the kernel runs `/init`; with a
  real root the kernel mounts `root=` and runs `/sbin/init` (BusyBox), which reads
  `/etc/inittab`. Mention `init=` / `rdinit=` for overriding and `init=/bin/sh` for rescue.
* [ ] **T19.4** Verify: staged tree layout correct, `rcS` executable, no device nodes needed.
  Snapshot as `ch19/`.

### Phase 10 — The ext2 image

* [ ] **T20.1** Implement `meta-core/classes/image.bbclass`:
  * `IMAGE_INSTALL` variable + `do_rootfs[deptask] = "do_populate_sysroot"` (or an explicit
    `DEPENDS` built from `IMAGE_INSTALL` in an anonymous Python function),
  * `do_rootfs` assembling `${IMAGE_ROOTFS}` from the staged components,
  * `do_image` driving `IMAGE_FSTYPES` → `IMAGE_CMD:<type>`, so the filesystem type is data,
    not hard-coded logic,
  * `IMAGE_CMD:ext2` = `mke2fs -t ext2 -b 1024 -L ${IMAGE_LABEL} -d ${IMAGE_ROOTFS}
    -F ${IMGDEPLOYDIR}/${IMAGE_NAME}.ext2 ${IMAGE_ROOTFS_SIZE}` — **no sudo, no loop mount**,
  * `IMAGE_CMD:cpio.gz` kept as a second type to prove the mechanism generalises,
  * `do_rootfs[cleandirs] = "${IMAGE_ROOTFS}"`, `do_image[dirs]`, stamp/`nostamp` policy,
  * `do_deploy` of the artifact plus a `rootfs.ext2` → `${IMAGE_NAME}.ext2` symlink.
* [ ] **T20.2** Write `recipes-core/images/simple-image.bb`:
  `IMAGE_INSTALL = "busybox base-files linux"`, `IMAGE_FSTYPES = "ext2"`, `inherit image`.
* [ ] **T20.3** Document ext2-specific gotchas:
  * why size is fixed up front (`IMAGE_ROOTFS_SIZE`, power of two for the SD model) and how
    to compute a size from the rootfs with `du -ks` plus `IMAGE_OVERHEAD_FACTOR`,
  * `mke2fs -d` needs e2fsprogs ≥ 1.43; `genext2fs -d` is the fallback,
  * ownership is the build user's uid unless a device/permission table is used — acceptable
    here because everything runs as root in the guest; note what Yocto does (pseudo),
  * no device nodes in the image → devtmpfs (Ch18) is what makes this work,
  * ext2 (no journal) is chosen over ext4 to keep kernel config and `mke2fs` options minimal.
* [ ] **T20.4** Document the deliberate simplification: no package manager, no `PACKAGES`
  splitting — components are staged and copied wholesale.
* [ ] **T20.5** Verify: `bitbake simple-image` produces
  `tmp/deploy/images/versatilepb/{zImage,versatile-pb.dtb,rootfs.ext2}`, and
  `dumpe2fs -h rootfs.ext2` plus `debugfs -R "ls -l /" rootfs.ext2` show the expected root
  (`sbin/init`, `etc/inittab`). Snapshot as `ch20/`.

### Phase 11 — Boot, debug, iterate

* [ ] **T21.1** Add `recipes-core/qemu/runqemu_1.0.bb` with `addtask run`,
  `do_run[nostamp] = "1"`, `do_run[depends] = "simple-image:do_image"`, launching:

      qemu-system-arm -M ${QEMU_MACHINE} -m ${QEMU_MEM} \
          -kernel ${DEPLOY_DIR_IMAGE}/${KERNEL_IMAGETYPE} \
          -dtb ${DEPLOY_DIR_IMAGE}/versatile-pb.dtb \
          -drive file=${DEPLOY_DIR_IMAGE}/rootfs.ext2,if=sd,format=raw \
          -serial stdio -display none \
          -append "${QEMU_APPEND}"

  Also emit a standalone `runqemu.sh` into the deploy dir, and a `--read-only`/snapshot
  variant (`-snapshot`) so students can throw away guest writes.
* [ ] **T21.2** Expected boot transcript in the doc (kernel log → `mmc0: new SD card` →
  `VFS: Mounted root (ext2 filesystem)` → rcS banner → `/ #` prompt), how to exit QEMU
  (`Ctrl-A X`), and a **persistence demo**: create a file, `poweroff`, re-run without
  `-snapshot`, and the file is still there — the payoff of ext2 over initramfs.
* [ ] **T21.3** Troubleshooting section, ext2-specific first:
  * `VFS: Unable to mount root fs on unknown-block(0,0)` → wrong `root=`, missing
    `CONFIG_MMC_BLOCK`, or the drive not attached as `if=sd`,
  * `Kernel panic – not syncing: No working init found` → `/sbin/init` missing or BusyBox
    not built with `CONFIG_INIT`,
  * no console output after mount → devtmpfs fragment not applied (no `/dev/console`),
  * `mke2fs: Filesystem larger than apparent device size` / image full → raise
    `IMAGE_ROOTFS_SIZE`,
  * QEMU refusing a non-power-of-two SD image,
  * plus the generic ones: dtb path changes across kernel versions, non-static BusyBox,
    wrong `console=`.
* [ ] **T21.4** Debugging toolbox recap: `bitbake -e recipe`, `-g`, `-DDD`, `-c listtasks`,
  reading `log.do_*`, `bitbake-layers show-appends`, and inspecting the image offline with
  `debugfs`.
* [ ] **T21.5** Verify end-to-end on a clean checkout: `bitbake simple-image && bitbake -c run runqemu`.
  Snapshot as `ch21/`.

### Phase 12 — Wrap-up and exercises

* [ ] **T22.1** Rewrite Chapter 10 "Summary" as Chapter 22: what was built, and an honest map
  of what Yocto/OE adds on top (sstate cache, packaging + `PACKAGES`/`FILES`, recipe-specific
  sysroots, toolchain recipes, pseudo/fakeroot for ownership and device nodes, `wic`, QA
  checks, `bitbake-layers create-layer`, multiconfig).
* [ ] **T22.2** Add graded exercises:
  * add `cpio.gz` to `IMAGE_FSTYPES` and boot the same rootfs as an initramfs (the README's
    original approach) — one variable, two image types,
  * switch the root device to SCSI (`if=scsi`, `root=/dev/sda`) by adding
    `CONFIG_SCSI`/`CONFIG_BLK_DEV_SD`/`CONFIG_SCSI_SYM53C8XX_2`/`CONFIG_PCI_VERSATILE`
    to a fragment — teaches BSP work,
  * add an ext4 image type (`IMAGE_CMD:ext4` + kernel `CONFIG_EXT4_FS`),
  * add a kernel config fragment via `.bbappend` from another layer,
  * add a second image recipe with a different `IMAGE_INSTALL`.
* [ ] **T22.3** Update `bitbakers/README.md` chapter list (ch11–ch21) and usage instructions.
* [ ] **T22.4** Cross-link `README.simple-linux-distro` ↔ tutorial: "manual steps here,
  automated by Chapters 11–21", and state the two intentional differences (newer versions,
  ext2 root instead of initramfs) with a pointer to the exercise that restores the initramfs.

## 6. Verification matrix (definition of done)

Commands run from `chNN/build`; artifacts land in the shared `shared/tmp` and
`shared/downloads` (§3.1), so Chapters 19–21 must reuse the kernel built in Chapter 18.

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

## 7. Decisions (all resolved)

1. ~~**Cross toolchain**~~ — **DECIDED**: use the host's `gcc-arm-linux-gnueabi` package.
   No toolchain recipes; Chapter 14 only configures and sanity-checks it, and Chapter 22
   notes that building a toolchain is what OE-Core adds.
2. ~~**Versions**~~ — **DECIDED**: track the latest upstream releases, pinned for
   reproducibility: **Linux 7.2.6** (stable, 2026-09-14) and **BusyBox 1.38.0** (2026-05-13),
   with checksums in T0.7 and a documented bump procedure. Verified against 7.2.6 sources:
   `versatile_defconfig` exists and sets `CONFIG_EXT2_FS=y`, `CONFIG_MMC=y`,
   `CONFIG_MMC_ARMMMCI=y`; `arch/arm/boot/dts/arm/versatile-pb.dts` still exists; there is
   **no** devtmpfs and **no** SCSI in that defconfig, hence the Ch18 fragment.
3. ~~**Root filesystem format**~~ — **DECIDED**: **ext2 on a virtual SD card**
   (`if=sd` → `/dev/mmcblk0`), built rootless with `mke2fs -d`. SD is chosen over SCSI
   because `versatile_defconfig` already has the MMC driver, so only devtmpfs needs a
   fragment; the SCSI variant becomes an exercise (T22.2). `cpio.gz` stays implemented as a
   second `IMAGE_FSTYPES` value to demonstrate that image types are pluggable.
4. ~~**Chapter snapshots**~~ — **DECIDED**: keep full `chNN/` snapshots, consistent with
   ch04–ch09, so each chapter is runnable and diffable. The duplication cost is avoided by
   sharing one `TMPDIR`/`DL_DIR` across Part II (§3.1), which requires `basichash` +
   `BB_BASEHASH_IGNORE_VARS` and the additive rule enforced by T0.5.
5. ~~**Demo recipes in Ch12–Ch16**~~ — **DECIDED**: use throwaway `hellosrc`/`hellodemo`/
   `libdemo`+`appdemo` recipes. Clearer learning: each mechanism is met on a recipe that
   builds in seconds, so the first long build (BusyBox, Ch17) happens only after fetch,
   task chains, cross-compilation, machine config and sysroots are already understood.
6. ~~**Build artifacts**~~ — **DECIDED**: git-ignored via T0.4; only metadata is versioned.
