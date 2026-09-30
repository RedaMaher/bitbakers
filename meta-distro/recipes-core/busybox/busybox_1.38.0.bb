SUMMARY = "Static BusyBox utilities and init"
LICENSE = "GPL-2.0-only"
inherit component

SRC_URI = "https://busybox.net/downloads/busybox-${PV}.tar.bz2"
SRC_URI[sha256sum] = "34f9ea6ff8636f2c9241153b9114eefa9e65674a45318ae1ef95bb5f31c53bb2"

do_configure() {
    make -C "${S}" O="${B}" ARCH=arm CROSS_COMPILE=${TARGET_PREFIX} defconfig
    sed -i -e 's/# CONFIG_STATIC is not set/CONFIG_STATIC=y/' \
        -e 's/CONFIG_TC=y/# CONFIG_TC is not set/' "${B}/.config"
    make -C "${S}" O="${B}" ARCH=arm CROSS_COMPILE=${TARGET_PREFIX} oldconfig < /dev/null
    for option in CONFIG_STATIC CONFIG_INIT CONFIG_ASH CONFIG_MOUNT CONFIG_POWEROFF; do
        grep -qx "$option=y" "${B}/.config" || bbfatal "Missing $option=y"
    done
    grep -qx '# CONFIG_TC is not set' "${B}/.config" || bbfatal "tc must be disabled"
}
do_compile() {
    make -C "${S}" O="${B}" ARCH=arm CROSS_COMPILE=${TARGET_PREFIX} \
        EXTRA_CFLAGS="-march=armv5te -marm" ${PARALLEL_MAKE}
    if ${TARGET_PREFIX}readelf -l "${B}/busybox" | grep -q INTERP; then
        bbfatal "BusyBox must not need a dynamic loader"
    fi
}
do_install() {
    make -C "${S}" O="${B}" ARCH=arm CROSS_COMPILE=${TARGET_PREFIX} \
        EXTRA_CFLAGS="-march=armv5te -marm" ${PARALLEL_MAKE} CONFIG_PREFIX="${D}" install
}
