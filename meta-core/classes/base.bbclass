bbfatal() {
    echo "ERROR: $*" >&2
    exit 1
}

do_build() {
    :
}
do_build[noexec] = "1"
addtask build

python do_listtasks() {
    for name in sorted(d.keys()):
        if d.getVarFlag(name, "task"):
            bb.plain(name)
}
do_listtasks[nostamp] = "1"
addtask listtasks
