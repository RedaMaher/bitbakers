inherit build

do_stage() {
    cp -a "${D}/." "${COMPONENTS_DIR}/${PN}/"
}
do_stage[cleandirs] = "${COMPONENTS_DIR}/${PN}"
addtask stage after do_install before do_build
