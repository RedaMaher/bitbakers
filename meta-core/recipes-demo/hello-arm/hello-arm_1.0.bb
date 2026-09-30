SUMMARY = "A tiny static ARM executable"
inherit build

SRC_URI = "file://hello.c"

do_compile() {
    ${TARGET_PREFIX}gcc -march=armv5te -marm -static -Os \
        "${WORKDIR}/hello.c" -o "${B}/hello-arm"
}
do_install() {
    install -Dm755 "${B}/hello-arm" "${D}/usr/bin/hello-arm"
}
