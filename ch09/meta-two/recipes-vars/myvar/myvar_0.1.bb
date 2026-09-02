DESCRIPTION = "Show access to global MYVAR"
PR = "r1"

do_build(){
  echo "myvar_sh: ${MYVAR}"
}

python do_myvar_py () {
  print ("myvar_py:" + d.getVar('MYVAR'))
}

addtask myvar_py before do_build