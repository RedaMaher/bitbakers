# BitBaker: standalone BitBake to a bootable ARM system

Build a small Linux system using **BitBake itself**, our own configuration and
classes, and upstream Linux and BusyBox sources. No Yocto Project checkout,
OpenEmbedded metadata, previous tutorial, or existing embedded distribution is
required.

This is one complete reference project, explored progressively in
[TUTORIAL.md](TUTORIAL.md), starting at Chapter 1. The tutorial explains the
bundled files before building each target; it does not maintain separate copies
of the project for each chapter.

## The system

| Part | Choice |
| --- | --- |
| Build engine | BitBake 2.18.0, pinned by commit in [`scripts/bootstrap`](scripts/bootstrap) |
| Board | QEMU ARM VersatilePB, ARM926/ARMv5, 128 MiB RAM |
| Kernel | Linux 7.2.6, built-in storage, ext2 and serial-console support |
| Userspace | BusyBox 1.38.0, statically linked for ARMv5 |
| Root filesystem | Writable 64 MiB ext2 image, attached as an SD card |
| Boot | QEMU loads `zImage` and `versatile-pb.dtb` directly; no bootloader or initramfs |
| Toolchain | Host-provided `arm-linux-gnueabi-` cross-toolchain |

“Complete” means a minimal bootable system with init, a console shell and
persistent storage—not a production distribution. This project does not build
its compiler, package manager, network services or production hardening.
There is no compiler-sysroot management or binary-package feed. Component
staging is simply preparation of target files for the image.

## Start here

Read [Chapter 1](TUTORIAL.md#chapter-1--one-project-from-an-empty-directory),
then provision the host using
[Chapter 2](TUTORIAL.md#chapter-2--prepare-the-linux-host).
Python 3.9 or newer and the `en_US.UTF-8` locale are required.

From this repository's root, after host provisioning:

```sh
scripts/check-host
scripts/bootstrap
scripts/bb hello
scripts/bb hello-arm
scripts/bb linux
scripts/bb busybox
scripts/bb base-files
scripts/bb simple-image
scripts/run-qemu
```

The kernel and userspace have been built, and the two-boot writable-ext2
persistence smoke test has passed. See the validation details below and in
Chapter 16. Tutorial command descriptions remain expected results for your
run, not a claim of a second full rebuild from a clean checkout. The first
source builds require network access, disk space and time.

The image build also schedules its required BusyBox, base-files and kernel
tasks automatically. `hello-arm` is a separate teaching target; it is not
installed in the default image.
Chapter 14 includes an optional exercise that stages `hello-arm`, selects it
with `IMAGE_INSTALL` in `local.conf`, and runs it at the guest console.

Expected deploy directory:

```text
build/tmp/deploy/images/versatilepb/
├── zImage
├── versatile-pb.dtb
├── rootfs.ext2
└── run-qemu.sh
```

The image task generates `run-qemu.sh` from machine configuration. Both the
interactive wrapper and automated smoke test use this same launcher.
The deployed DTB is built from our
[QEMU-specific board description](meta-bsp/recipes-kernel/linux/files/qemu-versatile-pb.dts),
which corrects SD card detection and interrupt wiring relative to the
upstream physical-board DTS. It is not a physical-hardware portability or
SD hotplug claim.

Normal QEMU runs write to `rootfs.ext2`. Use `scripts/run-qemu --snapshot` to
discard that run's disk writes. Shut the guest down with `poweroff`, wait for
`System halted instead`, then press Ctrl-a followed by x to exit QEMU.
See the tutorial before testing persistence or rebuilding an image containing data.

## Find the implementation

| Location | Responsibility |
| --- | --- |
| [`build/conf/bblayers.conf`](build/conf/bblayers.conf), [`local.conf`](build/conf/local.conf) | Layer selection and local choices |
| [`meta-core/conf/bitbake.conf`](meta-core/conf/bitbake.conf) | Our minimal BitBake configuration |
| [`meta-core/classes/base.bbclass`](meta-core/classes/base.bbclass) | Default build target and task listing |
| [`meta-core/classes/build.bbclass`](meta-core/classes/build.bbclass) | Fetch/configure/compile/install chain |
| [`meta-core/classes/component.bbclass`](meta-core/classes/component.bbclass) | Per-component target-file staging |
| [`meta-core/classes/image.bbclass`](meta-core/classes/image.bbclass) | Image dependencies and collision-checked assembly |
| [`meta-core/conf/machine/versatilepb.conf`](meta-core/conf/machine/versatilepb.conf) | Machine settings |
| [`meta-core/conf/distro/bitbaker.conf`](meta-core/conf/distro/bitbaker.conf) | Distribution identity and image size |
| [`meta-bsp/recipes-kernel/linux/linux_7.2.6.bb`](meta-bsp/recipes-kernel/linux/linux_7.2.6.bb) | Kernel configuration, build and deploy |
| [`qemu-versatile-pb.dts`](meta-bsp/recipes-kernel/linux/files/qemu-versatile-pb.dts) | QEMU-specific SD controller description |
| [`meta-distro/recipes-core/busybox/busybox_1.38.0.bb`](meta-distro/recipes-core/busybox/busybox_1.38.0.bb) | Static target utilities |
| [`meta-distro/recipes-core/base-files/base-files_1.0.bb`](meta-distro/recipes-core/base-files/base-files_1.0.bb) | Init policy and directories |
| [`meta-distro/recipes-core/images/simple-image.bb`](meta-distro/recipes-core/images/simple-image.bb) | Final image target |
| [`scripts/make-image.py`](scripts/make-image.py) | Unprivileged ext2 creation, root ownership and filesystem checking |
| [`scripts/run-qemu`](scripts/run-qemu) | Direct kernel boot with SD storage |

The repository is standalone even when placed inside another checkout. Its
commands use this directory, not any parent repository. Bootstrap fetches only
BitBake into `tools/bitbake`; it does not create a project Git commit or remote.
Original tutorial content, metadata and scripts are covered by the
[MIT license](LICENSE), copyright 2026 BitBaker contributors. Downloaded
BitBake, Linux, BusyBox, toolchains and other upstream software retain their
own licenses. Recipe `LICENSE` fields describe licensing; this project does
not implement automated license compliance.

## Checks and iteration

```sh
scripts/bb -c listtasks hello
scripts/bb -e hello
scripts/bb -C configure busybox
scripts/bb simple-image
```

There is **no `clean` task** in these minimal classes. The tutorial explains
task invalidation, logs, image replacement and safe clean-checkout rebuilding.
Do not assume utilities such as `bitbake-layers` work with this deliberately
small, non-OE configuration; use `scripts/bb` for the documented interface.

Available validation commands are:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/smoke-test.py
```

Observed validation:

- All five [`image tests`](tests/test_image.py) passed with 256-byte inodes,
  including real ext2 creation, contents, ownership, modes, symlinks and replacement.
- Kernel and userspace built; static ARMv5 ELF output was verified.
- `rootfs.ext2` is exactly 67,108,864 bytes.
- The [`smoke test`](scripts/smoke-test.py) passed both `WRITE-OK` and
  `PERSISTENCE-OK` on a **copy** of the image; serial logs are under
  `build/tmp/test-logs/`.
- A repeated `hello-arm` + `simple-image` build skipped all 27 tasks.
- An additional ad hoc check booted `scripts/run-qemu --snapshot`, wrote
  `/root/snapshot-check`, synced and halted; the original image's SHA-256
  remained identical. This check is separate from the delivered smoke test.

The final five-test image suite and two-boot smoke test were both rerun
successfully.

Validation used Python 3.14.4, GCC 15.2.0, QEMU 10.2.1 and e2fsprogs 1.47.2.
Missing host packages were extracted locally for validation without `sudo`;
normal readers should follow Chapter 2's package provisioning. A second full
clean-checkout rebuild has not been performed. See
[Chapter 16](TUTORIAL.md#chapter-16--validation-and-a-clean-checkout)
for the validation environment and reproduction instructions.
