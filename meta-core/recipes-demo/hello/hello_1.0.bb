SUMMARY = "First task: no compiler or downloads required"

do_greet() {
    echo "Hello from standalone BitBake!"
}
addtask greet before do_build
