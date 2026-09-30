#!/usr/bin/env python3
"""Build an ext2 SD image without mounts, device nodes, or elevated privileges."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile


def make_image(root: Path, output: Path, size_kib: int, label: str) -> None:
    if size_kib < 8192 or size_kib & (size_kib - 1):
        raise ValueError("SD image size must be a power of two, at least 8192 KiB")
    if not root.is_dir():
        raise ValueError(f"Root filesystem directory does not exist: {root}")
    if not label or len(label.encode()) > 16:
        raise ValueError("ext2 label must contain 1 to 16 bytes")

    commands = ['set_inode_field "/" uid 0', 'set_inode_field "/" gid 0']
    for directory, dirs, files in os.walk(root):
        for name in sorted(dirs + files):
            path = "/" + (Path(directory) / name).relative_to(root).as_posix()
            if any(char in path for char in ('"', "\\", "\n", "\r")):
                raise ValueError(f"Unsupported debugfs pathname: {path!r}")
            commands.extend(
                f'set_inode_field "{path}" {field} 0' for field in ("uid", "gid")
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    # Publish only a fully populated and checked filesystem.
    with tempfile.TemporaryDirectory(prefix=".image-", dir=output.parent) as temp:
        image = Path(temp) / "rootfs.ext2"
        batch = Path(temp) / "ownership.debugfs"
        batch.write_text("\n".join(commands) + "\n")
        with image.open("wb") as stream:
            stream.truncate(size_kib * 1024)
        subprocess.run(
            ["mke2fs", "-q", "-t", "ext2", "-b", "1024", "-I", "256",
             "-O", "none,filetype,sparse_super,large_file", "-m", "0",
             "-E", "root_owner=0:0", "-L", label, "-d", str(root), "-F", str(image)],
            check=True,
        )
        result = subprocess.run(
            ["debugfs", "-w", "-f", str(batch), str(image)],
            check=True, text=True, capture_output=True,
        )
        # debugfs may print command errors while still returning exit status zero.
        errors = [
            line for line in result.stderr.splitlines()
            if line.strip() and not line.startswith("debugfs ")
        ]
        if errors:
            raise RuntimeError("debugfs ownership update failed:\n" + "\n".join(errors))
        subprocess.run(["e2fsck", "-fn", str(image)], check=True)
        os.replace(image, output)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        sys.exit("Usage: make-image.py ROOTFS OUTPUT SIZE_KIB LABEL")
    make_image(Path(sys.argv[1]), Path(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
