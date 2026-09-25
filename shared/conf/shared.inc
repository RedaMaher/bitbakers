BBGUIDE_SHARED := "${@os.path.normpath(d.getVar('TOPDIR') + '/../../shared')}"

DL_DIR  = "${BBGUIDE_SHARED}/downloads"
TMPDIR  = "${BBGUIDE_SHARED}/tmp"

BB_NUMBER_THREADS ?= "4"
PARALLEL_MAKE     ?= "-j 8"

BB_SIGNATURE_HANDLER = "basichash"
BB_BASEHASH_IGNORE_VARS += "TMPDIR DL_DIR TOPDIR FILE FILE_DIRNAME THISDIR \
                            LAYERDIR BBPATH PATH PWD DATE TIME \
                            BB_NUMBER_THREADS PARALLEL_MAKE BB_TASKHASH"
