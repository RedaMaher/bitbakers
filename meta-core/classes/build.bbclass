inherit fetch

do_configure() {
    :
}
do_compile() {
    :
}
do_install() {
    :
}
do_configure[dirs] = "${B}"
do_compile[dirs] = "${B}"
do_install[dirs] = "${B}"
do_install[cleandirs] = "${D}"
addtask configure after do_unpack before do_build
addtask compile after do_configure before do_build
addtask install after do_compile before do_build
