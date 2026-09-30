IMAGE_ROOTFS = "${WORKDIR}/rootfs"
IMAGE_INSTALL ?= "busybox base-files"
IMAGE_BUILDER = "${TOPDIR}/../scripts/make-image.py"

python do_rootfs() {
    import os
    import shutil
    root = d.getVar("IMAGE_ROOTFS")
    for component in d.getVar("IMAGE_INSTALL").split():
        source = os.path.join(d.getVar("COMPONENTS_DIR"), component)
        if not os.path.isdir(source):
            bb.fatal("Missing staged component: " + source)
        for directory, dirs, files in os.walk(source):
            for name in dirs + files:
                src = os.path.join(directory, name)
                dst = os.path.join(root, os.path.relpath(src, source))
                if os.path.lexists(dst) and not (
                    os.path.isdir(src) and not os.path.islink(src)
                    and os.path.isdir(dst) and not os.path.islink(dst)
                ):
                    bb.fatal("Rootfs collision: " + dst)
        shutil.copytree(source, root, symlinks=True, dirs_exist_ok=True)
}
do_rootfs[cleandirs] = "${IMAGE_ROOTFS}"
do_rootfs[depends] = "${@' '.join(p + ':do_stage' for p in d.getVar('IMAGE_INSTALL').split())}"

do_image() {
    python3 "${IMAGE_BUILDER}" "${IMAGE_ROOTFS}" \
        "${DEPLOY_DIR_IMAGE}/rootfs.ext2" "${IMAGE_ROOTFS_SIZE}" "${IMAGE_LABEL}"
    cat > "${DEPLOY_DIR_IMAGE}/run-qemu.sh" <<'EOF'
#!/bin/sh
set -eu
deploy=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec qemu-system-arm -M ${QEMU_MACHINE} -m ${QEMU_MEM} \
    -kernel "$deploy/zImage" -dtb "$deploy/versatile-pb.dtb" \
    -display none -serial mon:stdio -nic none -audio driver=none \
    -append "${QEMU_APPEND}" "$@"
EOF
    chmod 755 "${DEPLOY_DIR_IMAGE}/run-qemu.sh"
}
do_image[dirs] = "${DEPLOY_DIR_IMAGE}"
do_image[file-checksums] = "${IMAGE_BUILDER}:True"
do_image[depends] = "linux:do_deploy"
addtask rootfs before do_image
addtask image after do_rootfs before do_build
