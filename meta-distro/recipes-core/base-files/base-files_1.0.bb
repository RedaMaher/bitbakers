SUMMARY = "Directories and boot policy"
LICENSE = "MIT"
inherit component

SRC_URI = "file://inittab file://rcS file://fstab file://profile"

do_install() {
    for dir in bin sbin etc/init.d proc sys dev tmp run root usr/bin usr/sbin var/log; do
        install -d "${D}/$dir"
    done
    chmod 1777 "${D}/tmp"
    chmod 700 "${D}/root"
    install -m644 "${WORKDIR}/inittab" "${D}/etc/inittab"
    install -m755 "${WORKDIR}/rcS" "${D}/etc/init.d/rcS"
    install -m644 "${WORKDIR}/fstab" "${D}/etc/fstab"
    install -m644 "${WORKDIR}/profile" "${D}/etc/profile"
    printf 'NAME="%s"\nVERSION="%s"\nID=bitbaker\n' \
        "${DISTRO_NAME}" "${DISTRO_VERSION}" > "${D}/etc/os-release"
}
