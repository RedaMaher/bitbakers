#!/usr/bin/env bash

set -e

if [ "$#" -lt 2 ]; then
    echo "Usage: $0 <chNN> <targets...>"
    exit 1
fi

chapter="$1"
shift

repo_root="$(cd "$(dirname "$0")/.." && pwd)"

source "$repo_root/bbenv.include"

build_dir="$repo_root/$chapter/build"

if [ ! -d "$build_dir" ]; then
    echo "ERROR: Chapter build directory not found:"
    echo "  $build_dir"
    exit 1
fi

cd "$build_dir"

echo "Running: bitbake $*"
bitbake "$@"
