# A Practical Guide to BitBake

## Updated for BitBake 2.18 and Python 3.14

**Contents**

1.  [Preface](#1-preface)
2.  [BitBake](#2-bitbake)
3.  [Setup BitBake](#3-setup-bitbake)
4.  [Create a project](#4-create-a-project)
5.  [The first recipe](#5-the-first-recipe)
6.  [Classes and functions](#6-classes-and-functions)
7.  [BitBake layers](#7-bitbake-layers)
8.  [Share and reuse configurations](#8-share-and-reuse-configurations)
9.  [Using variables](#9-using-variables)
10. [Summary](#10-summary)

## 1. Preface

### 1.1 About this tutorial

BitBake is used mainly by OpenEmbedded and the Yocto Project to build Linux distributions, and it has a fairly steep learning curve. This tutorial exists to flatten that curve.

It does not try to cover everything about BitBake — that isn’t really possible — but it explains the fundamentals well enough that you can start writing your own recipes.

### 1.2 Target of this tutorial

The tutorial builds the smallest possible project and extends it step by step, to show and explain how BitBake actually works.

### 1.3 Acknowledgments

The learning sequence is inspired by Harald Achitz’s original “A Practical Guide to BitBake.” Issues for the accompanying example repository can be reported at the [BitBake guide issue tracker](https://bitbucket.org/a4z/bitbakeguide/issues).


## 2. BitBake

### 2.1 What is BitBake

BitBake is, at its core, a Python program: driven by configuration you write, it executes tasks you define for specified targets, called recipes.

### 2.1.1 Config, tasks and recipes

Configuration, tasks, and recipes are written in BitBake’s own small language — variables plus shell or Python code. Since BitBake actually executes that code, it could in theory be used for things other than building software, though that’s probably not a great idea.

BitBake was built for building software, so it has features suited to that: it can resolve dependencies and put tasks into the right order. Building software packages also tends to repeat the same kinds of steps — downloading and extracting source, running configure, running make, writing a log message — and BitBake gives you a way to abstract, encapsulate, and reuse that work in a configurable way.

## 3. Setup BitBake

BitBake is available at [github.com/openembedded/bitbake](https://github.com/openembedded/bitbake). This tutorial was tested with Python 3.14.4 and BitBake 2.18.0 on Ubuntu 26.04 — if you hit a problem with a different combination, please report it (see 1.4). When BitBake is used inside a full Yocto/OpenEmbedded build it is normally bundled with the layers and started through the project’s own setup script; here we install the standalone `bitbake-2.18.0` release directly, so the engine underneath stays visible.

Download the tagged [2.18.0 release](https://github.com/openembedded/bitbake/archive/refs/tags/2.18.0.zip) and extract it.

### 3.1 The installation of BitBake

The installation is very simple:

- Add the extracted folder’s `bin` directory to `PATH`.
- Add its `lib` directory to `PYTHONPATH`.

We can do this by running:

    export PATH="/path/to/bitbake-2.18.0/bin:$PATH"
    export PYTHONPATH="/path/to/bitbake-2.18.0/lib:$PYTHONPATH"

These commands configure BitBake for the current terminal session. If you open a new terminal, you must run them again.

First we check that everything works and BitBake is installed. To do that, run:

    bitbake --version

Expected output:

    BitBake Build Tool Core version 2.18.0

#### 3.1.1 Ubuntu permission check

On Ubuntu, check whether the user namespace operation required by modern BitBake is allowed:

    unshare --user --map-root-user true

If the command finishes silently, continue normally. If it reports “write failed /proc/self/uid_map: Operation not permitted”, Ubuntu’s AppArmor policy is blocking the operation. Only in that case, apply this temporary workaround:

    echo 0 | sudo tee /proc/sys/kernel/apparmor_restrict_unprivileged_userns

Then run the unshare check again. This command temporarily relaxes a system-wide Ubuntu security restriction until the next reboot; it is not a BitBake setting and should not be used on systems where the check already succeeds.

### 3.2 The BitBake documentation

From the extracted folder you can build the manual yourself with `make html DOC=bitbake-user-manual` (run from its `doc` directory), or read it online. Use the versioned [BitBake 2.18 User Manual](https://docs.yoctoproject.org/bitbake/2.18/) so it matches the version used here.

## 4. Create a project

### 4.1 BitBake project layout

We will create:

    bbTutorial/
    ├── build/
    │   └── conf/
    │       └── bblayers.conf
    └── meta-tutorial/
        ├── classes/
        │   └── base.bbclass
        └── conf/
            ├── bitbake.conf
            └── layer.conf

The `build` directory is where we run BitBake. `meta-tutorial` is a **layer** — a folder of related configuration, recipes, classes, and append files, conventionally prefixed `meta-`.

### 4.2 The smallest possible project

First create the directories:

    mkdir -p "$HOME/bbTutorial/build/conf"
    mkdir -p "$HOME/bbTutorial/meta-tutorial/classes"
    mkdir -p "$HOME/bbTutorial/meta-tutorial/conf"

#### 4.2.1 The required config files

First a description of the needed files, then a short description of their content.

**build/conf/bblayers.conf**

The first file BitBake expects is `conf/bblayers.conf` in its working directory, which is our build directory. For now we create it with this content:

    BBPATH := "${TOPDIR}"
    BBFILES ?= ""
    BBLAYERS = "${TOPDIR}/../meta-tutorial"

**meta-tutorial/conf/layer.conf**

Each layer needs a `conf/layer.conf` file. For now we create it with this content:

    BBPATH .= ":${LAYERDIR}"
    BBFILES += "${LAYERDIR}/recipes-*/*/*.bb"

**meta-tutorial/classes/base.bbclass and meta-tutorial/conf/bitbake.conf**

For now, these files can be taken from the BitBake installation directory. They’re located in the folders bitbake-2.18.0/classes and bitbake-2.18.0/conf. Simply copy them into the tutorial project.

#### 4.2.2 Some notes on the created files

**build/conf/bblayers.conf**

Add the current working directory to `BBPATH` by assigning it to `TOPDIR` — `TOPDIR` is set internally by BitBake to the current working directory. Initialize `BBFILES` as empty; recipes will be added later. Add the path of our `meta-tutorial` layer to `BBLAYERS` — when it runs, BitBake searches every listed layer directory for further configuration.

**meta-tutorial/conf/layer.conf**

`LAYERDIR` is a variable BitBake passes to the layer it loads; we append this path to `BBPATH`. `BBFILES` tells BitBake where recipes are — we append nothing yet, since we have none, but that changes later. `.=` and `+=` append a value to a variable, without or with a separating space.

**conf/bitbake.conf**

For now we take this file’s variables as they are.

**classes/base.bbclass**

A `.bbclass` file holds shared functionality. Our `base.bbclass` provides some logging functions we’ll use later, and a `build` task that does nothing — not very useful yet, but required, since `build` is the task BitBake runs by default when no other task is specified. We’ll change this task later.

#### 4.2.3 BitBake search path

Some file paths BitBake looks for are relative to `BBPATH`: if we tell BitBake to search for a path, it checks every directory listed in `BBPATH` (which, like `PATH`, can hold several directories separated by `:`).

We’ve added `TOPDIR` and `LAYERDIR` to `BBPATH`, so `classes/base.bbclass` and `conf/bitbake.conf` could live in either — but we put them in `meta-tutorial`. The build directory should never hold general files, only build-specific ones like a `local.conf`, which we’ll use later.

### 4.3 The first run

In a terminal, change into the build directory we just created — that’s our working directory. We always run BitBake from there, so it can find the relative `conf/bblayers.conf` file.

    cd "$HOME/bbTutorial/build"
    bitbake

If the setup is correct, BitBake reports:

    Nothing to do. Use 'bitbake world' to build everything,
    or run 'bitbake --help' for usage information.

Not very useful on its own, but a good start — and a good moment to introduce a useful flag, verbose debug output:

    bitbake -vDDD world

The output should look similar to this:

    Loading cache: 100%
    Loaded 0 entries from dependency cache.
    DEBUG: collating packages for "world"
    DEBUG: Target list: []
    NOTE: Resolving any missing task queue dependencies
    DEBUG: Resolved 0 extra dependencies

You’ll see a stream of NOTE: and DEBUG: lines. -vDDD enables very detailed output, and world asks BitBake to build every available recipe. Since the project has no recipes yet, there are no build tasks to run; the useful part here is observing how BitBake parses the configuration. We add the first recipe in the next chapter.

Notice that BitBake also created a `tmp` directory alongside `conf/`.

## 5. The first recipe

BitBake needs recipes before it can do useful work. Check the current recipe list:


    bitbake -s
    
    Recipe Name          Latest Version        Preferred Version
    ===========          ==============        =================

The list is empty — we haven’t created a recipe yet.

### 5.1 The cache location

BitBake caches parsed metadata to make later commands faster. BitBake 2.18’s copied `bitbake.conf` already defines `CACHE`, so there is nothing to add here.

### 5.2 Adding a recipe location to the tutorial layer

BitBake finds recipes through `BBFILES`, which we already set in `meta-tutorial/conf/layer.conf`:

    BBFILES += "${LAYERDIR}/recipes-*/*/*.bb"

This means: look inside directories named `recipes-*`, then inside a recipe directory, and load files ending in `.bb`.

5.3 Create the first recipe and task

Recipe files follow the pattern `name_version.bb`. Create the directory:

    mkdir -p "$HOME/bbTutorial/meta-tutorial/recipes-tutorial/first"

Create `$HOME/bbTutorial/meta-tutorial/recipes-tutorial/first/first_0.1.bb`:




    DESCRIPTION = "I am the first recipe"
    PR = "r1"

    do_build () {
        echo "first: some shell script running as build"
    }

List the recipes and build `first`:

    cd "$HOME/bbTutorial/build"
    bitbake -s
    bitbake first

`bitbake -s` now shows:

    Recipe Name          Latest Version        Preferred Version
    ===========          ==============        =================
    first                       :0.1-r1

and the build summary should say every attempted task succeeded. The task log is at:

    build/tmp/work/first-0.1-r1/temp/log.do_build

and should contain:

    DEBUG: Executing shell function do_build
    first: some shell script running as build
    DEBUG: Shell function do_build finished

## 6. Classes and functions

### 6.1 Create the mybuild class

A `.bbclass` holds reusable metadata, so a task doesn’t have to be copied into every recipe that needs it. Create `$HOME/bbTutorial/meta-tutorial/classes/mybuild.bbclass`:

    addtask build

    mybuild_do_build () {
        echo "running mybuild_do_build."
    }

    EXPORT_FUNCTIONS do_build

`EXPORT_FUNCTIONS do_build` exposes `mybuild_do_build` as `do_build` to any recipe that inherits the class.

### 

### 6.2 Use mybuild with the second recipe

    mkdir -p "$HOME/bbTutorial/meta-tutorial/recipes-tutorial/second"

Create `$HOME/bbTutorial/meta-tutorial/recipes-tutorial/second/second_1.0.bb`:


    DESCRIPTION = "I am the second recipe"
    PR = "r1"

    inherit mybuild

    def pyfunc(o):
        print(dir(o))

    python do_mypatch () {
        bb.note("running mypatch")
        pyfunc(d)
    }

    addtask mypatch before do_build

This recipe shows three kinds of reuse: `inherit mybuild` pulls in the class’s metadata, `do_mypatch` is a Python task, and `pyfunc` is a plain Python helper the task calls. `d` is BitBake’s datastore — the variables visible in the current metadata context.

### 6.3 Exploring recipes and tasks


    bitbake -s

should now show:

    Recipe Name          Latest Version        Preferred Version
    ===========          ==============        =================
    first                       :0.1-r1
    second                      :1.0-r1

List a recipe’s tasks with:

    bitbake -c listtasks second

### 6.4 Executing tasks or building the world

    bitbake second
    bitbake -c mypatch second
    bitbake world

`bitbake second` runs the default build task and its predecessors; `-c mypatch` runs `do_mypatch` explicitly; `bitbake world` builds every recipe visible to the configuration. Task logs live under `build/tmp/work/<recipe>-<version>-<revision>/temp/`.

## 7. BitBake layers

A typical BitBake project has more than one layer, each covering a specific topic, and different build targets can combine layers differently. Layers let you extend, configure, and even partially override content from another layer, which is what makes them reusable.

### 7.1 Adding an additional layer

Create its directory:

    mkdir -p "$HOME/bbTutorial/meta-two/conf"

Create `$HOME/bbTutorial/meta-two/conf/layer.conf`:

    BBPATH .= ":${LAYERDIR}"
    BBFILES += "${LAYERDIR}/recipes-*/*/*.bb"

Then add it to `$HOME/bbTutorial/build/conf/bblayers.conf`:

    BBPATH := "${TOPDIR}"
    BBFILES ?= ""
    BBLAYERS = " \
        ${TOPDIR}/../meta-tutorial \
        ${TOPDIR}/../meta-two \
    "

### 7.2 The bitbake-layers command

    bitbake-layers show-layers

Other useful subcommands: `show-recipes`, `show-cross-depends`, `show-appends`, `flatten`, `show-overlayed`.

### 7.3 Extending the layer configuration

Add to `meta-tutorial/conf/layer.conf`:

    BBFILE_COLLECTIONS += "tutorial"
    BBFILE_PATTERN_tutorial = "^${LAYERDIR}/"
    BBFILE_PRIORITY_tutorial = "5"

Add to `meta-two/conf/layer.conf`:

    BBFILE_COLLECTIONS += "two"
    BBFILE_PATTERN_two = "^${LAYERDIR}/"
    BBFILE_PRIORITY_two = "5"
    LAYERVERSION_two = "1"

bitbake-layers show-layers should now list both layer collections with priority 5:

    layer       path                                  priority
    =============================================================
    tutorial    /home/user/bbTutorial/meta-tutorial    5
    two         /home/user/bbTutorial/meta-two         5

At this stage, BitBake can also warn that no .bb files match BBFILE_PATTERN_two. That is expected because meta-two is still empty; Chapter 8 adds its first recipe.

### 7.4 Layer compatibility

At this point BitBake 2.18 will warn that these layers have no declared layer-series compatibility.

#### 7.4.1 Layer series core name

Add to `meta-tutorial/conf/layer.conf`:

    LAYERSERIES_CORENAMES = "bitbakeguide"

#### 7.4.2 Layer series compatibility

Also in `meta-tutorial/conf/layer.conf`:

    LAYERVERSION_tutorial = "1"
    LAYERSERIES_COMPAT_tutorial = "bitbakeguide"

Add to `meta-two/conf/layer.conf`:

    LAYERSERIES_COMPAT_two = "bitbakeguide"

The project-defined series name must match in LAYERSERIES_CORENAMES and each layer’s LAYERSERIES_COMPAT entry.

### 7.5 Layer dependencies

Add to `meta-two/conf/layer.conf`:

    LAYERDEPENDS_two = "tutorial"

This tells BitBake that `meta-two` requires the layer collection named `tutorial`.

## 8. Share and reuse configurations

Besides classes and configuration files, BitBake lets you reuse and extend metadata through class inheritance, `.bbappend` files, and include files. This chapter adds a class in `meta-two` that builds a configure-then-build chain on top of `mybuild`, then extends an existing recipe from another layer.

### 8.1 Class inheritance

    mkdir -p "$HOME/bbTutorial/meta-two/classes"

Create `$HOME/bbTutorial/meta-two/classes/confbuild.bbclass`:

    inherit mybuild

    confbuild_do_configure () {
        echo "running confbuild_do_configure."
    }

    addtask do_configure before do_build
    EXPORT_FUNCTIONS do_configure

Create the third recipe:

    mkdir -p "$HOME/bbTutorial/meta-two/recipes-base/third"

`$HOME/bbTutorial/meta-two/recipes-base/third/third_0.1.2.bb`:

    DESCRIPTION = "I am the third recipe"
    PR = "r1"

    inherit confbuild
    cd "$HOME/bbTutorial/build"
    bitbake third

Both `do_configure` and `do_build` should succeed.

### 8.2 bbappend files

Update `meta-two/conf/layer.conf` so it also picks up append files:

    BBFILES += "${LAYERDIR}/recipes-*/*/*.bb \
                ${LAYERDIR}/recipes-*/*/*.bbappend"
    mkdir -p "$HOME/bbTutorial/meta-two/recipes-base/first"

Create `$HOME/bbTutorial/meta-two/recipes-base/first/first_0.1.bbappend`:

    python do_patch () {
        bb.note("first:do_patch")
    }

    addtask patch before do_build

Its filename matches `first_0.1.bb`, so BitBake merges this into that recipe — this is how one layer customizes a recipe owned by another without editing the original.


    bitbake-layers show-appends
    bitbake -c listtasks first
    bitbake first

### 8.3 Include files

Both directives search relative to `BBPATH`: `include file` parses it if present and continues if it’s absent; `require file` parses it and fails if it’s absent.

#### 8.3.1 Add a local.conf for inclusion

Add to `meta-tutorial/conf/bitbake.conf`:

    require local.conf
    include conf/might_exist.conf
    cd "$HOME/bbTutorial/build"
    bitbake first

BitBake reports that the required `local.conf` is missing. Create an empty one:

    touch "$HOME/bbTutorial/build/local.conf"
    bitbake first

The missing, optional `conf/might_exist.conf` never causes an error.

## 9. Using variables

Variables are what make BitBake recipes and classes configurable instead of hard-coded: a class can define a task that reads a variable, and each recipe that inherits it supplies its own value instead of editing the class itself.

### 9.1 Global variables

#### 9.1.1 Define global variables

Add to `$HOME/bbTutorial/build/local.conf`:

    MYVAR = "hello from MYVAR"

BitBake 2.18 warns if there is no whitespace around `=`, so keep the spaces.

#### 9.1.2 Accessing global variables

    mkdir -p "$HOME/bbTutorial/meta-two/recipes-vars/myvar"

Create `$HOME/bbTutorial/meta-two/recipes-vars/myvar/myvar_0.1.bb`:

    DESCRIPTION = "Show access to global MYVAR"
    PR = "r1"

    do_build () {
        echo "myvar_sh: ${MYVAR}"
    }

    python do_myvar_py () {
        print("myvar_py:" + d.getVar('MYVAR'))
    }

    addtask myvar_py before do_build

Shell tasks expand a variable as `${MYVAR}`; Python tasks read it from the datastore with `d.getVar()`.

    cd "$HOME/bbTutorial/build"
    bitbake myvar

Its log, under `build/tmp/work/myvar-0.1-r1/temp/`, should contain:

    myvar_py:hello from MYVAR
    myvar_sh: hello from MYVAR

### 9.2 Local variables

Create `$HOME/bbTutorial/meta-two/classes/varbuild.bbclass`:

    varbuild_do_build () {
        echo "build with args: ${BUILDARGS}"
    }

    addtask build
    EXPORT_FUNCTIONS do_build

The class knows the variable’s name but not its value.

    mkdir -p "$HOME/bbTutorial/meta-two/recipes-vars/varbuild"

Create `$HOME/bbTutorial/meta-two/recipes-vars/varbuild/varbuild_0.1.bb`:

    DESCRIPTION = "Demonstrate variable usage \
        for setting up a class task"
    PR = "r1"

    BUILDARGS = "my build arguments"

    inherit varbuild
    cd "$HOME/bbTutorial/build"
    bitbake varbuild

Its log should contain:

    build with args: my build arguments

## 10. Summary

This tutorial used BitBake as a standalone task engine to practice: what BitBake actually does; the build/layer project layout; recipes, classes, tasks, and task ordering; multiple layers and how they relate to each other; the five metadata file types; and global and recipe-local variables.
