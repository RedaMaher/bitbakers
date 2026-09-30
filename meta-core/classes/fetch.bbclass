python do_fetch() {
    bb.fetch2.Fetch((d.getVar("SRC_URI") or "").split(), d).download()
}
do_fetch[network] = "1"

python do_unpack() {
    bb.fetch2.Fetch((d.getVar("SRC_URI") or "").split(), d).unpack(d.getVar("WORKDIR"))
}
do_unpack[cleandirs] = "${S} ${B}"
do_unpack[dirs] = "${WORKDIR}"
do_fetch[file-checksums] = "${@bb.fetch2.get_checksum_file_list(d)}"
addtask fetch before do_build
addtask unpack after do_fetch before do_build
