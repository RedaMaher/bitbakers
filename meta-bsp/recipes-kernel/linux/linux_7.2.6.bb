SUMMARY = "Linux for QEMU ARM VersatilePB"
LICENSE = "GPL-2.0-only"
inherit build deploy

SRC_URI = "https://cdn.kernel.org/pub/linux/kernel/v7.x/linux-${PV}.tar.xz \
           file://versatilepb.cfg"
SRC_URI[sha256sum] = "039aef84f2b0994aeda3f4fcfc3d02ec9d7a9bbb9020ea264c43f446c860f606"
QEMU_DTS = "${FILE_DIRNAME}/files/qemu-versatile-pb.dts"

do_configure() {
    make -C "${S}" O="${B}" ARCH=arm CROSS_COMPILE=${TARGET_PREFIX} ${KERNEL_DEFCONFIG}
    "${S}/scripts/kconfig/merge_config.sh" -m -O "${B}" \
        "${B}/.config" "${WORKDIR}/versatilepb.cfg"
    make -C "${S}" O="${B}" ARCH=arm CROSS_COMPILE=${TARGET_PREFIX} olddefconfig
    while IFS= read -r option; do
        case "$option" in
            CONFIG_*=y) grep -qx "$option" "${B}/.config" || bbfatal "Missing $option" ;;
        esac
    done < "${WORKDIR}/versatilepb.cfg"
}
do_compile() {
    make -C "${S}" O="${B}" ARCH=arm CROSS_COMPILE=${TARGET_PREFIX} \
        ${PARALLEL_MAKE} zImage dtbs
}
do_devicetree() {
    gcc -E -P -x assembler-with-cpp -nostdinc -undef -D__DTS__ \
        -I "${S}/arch/arm/boot/dts/arm" -I "${S}/scripts/dtc/include-prefixes" \
        "${QEMU_DTS}" -o "${B}/qemu-versatile-pb.preprocessed.dts"
    "${B}/scripts/dtc/dtc" -I dts -O dtb \
        -o "${B}/${KERNEL_DEVICETREE}" "${B}/qemu-versatile-pb.preprocessed.dts"
}
do_devicetree[file-checksums] = "${QEMU_DTS}:True"
addtask devicetree after do_compile before do_deploy

do_deploy() {
    install -m644 "${B}/arch/arm/boot/zImage" "${DEPLOY_DIR_IMAGE}/zImage"
    install -m644 "${B}/${KERNEL_DEVICETREE}" \
        "${DEPLOY_DIR_IMAGE}/versatile-pb.dtb"
}
