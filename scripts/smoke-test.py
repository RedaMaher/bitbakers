#!/usr/bin/env python3
"""Boot twice against a disposable copy and verify actual ext2 persistence."""

from pathlib import Path
import selectors
import shutil
import subprocess
import tempfile
import time
import uuid


ROOT = Path(__file__).resolve().parents[1]
DEPLOY = ROOT / "build/tmp/deploy/images/versatilepb"


def boot(image: Path, command: str, expected: str, log: Path) -> None:
    args = [
        str(DEPLOY / "run-qemu.sh"),
        "-drive", f"file={image},if=sd,format=raw",
    ]
    with log.open("wb") as transcript, subprocess.Popen(
        args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
    ) as process, selectors.DefaultSelector() as selector:
        selector.register(process.stdout, selectors.EVENT_READ)
        output = b""
        sent = False
        deadline = time.monotonic() + 180
        try:
            while time.monotonic() < deadline:
                if process.poll() is not None:
                    raise RuntimeError(f"QEMU exited before verification; see {log}")
                for key, _ in selector.select(timeout=1):
                    chunk = key.fileobj.read1(65536)
                    transcript.write(chunk)
                    transcript.flush()
                    output += chunk
                if not sent and b"bitbaker:" in output and b" # " in output:
                    process.stdin.write((command + "\n").encode())
                    process.stdin.flush()
                    sent = True
                if sent and expected.encode() in output and b"reboot: System halted" in output:
                    print(f"PASS: {expected}; guest synced and halted ({log})")
                    return
            raise TimeoutError(f"Boot/persistence check timed out; see {log}")
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()


def main() -> None:
    for name in ("zImage", "versatile-pb.dtb", "rootfs.ext2", "run-qemu.sh"):
        if not (DEPLOY / name).is_file():
            raise FileNotFoundError(f"Missing {DEPLOY / name}; run scripts/bb simple-image")
    logs = ROOT / "build/tmp/test-logs"
    logs.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    with tempfile.TemporaryDirectory(prefix="bitbaker-smoke-") as temp:
        image = Path(temp) / "test.ext2"
        shutil.copyfile(DEPLOY / "rootfs.ext2", image)
        # Split printf arguments so the echoed input cannot satisfy the output check.
        boot(
            image,
            "grep -q ' / ext2 rw' /proc/mounts && "
            f"echo {token} > /root/persistence && sync && "
            "printf 'WRITE-%s\\n' OK; halt",
            "WRITE-OK", logs / "first-boot.log",
        )
        boot(
            image,
            f'test "$(cat /root/persistence)" = {token} && '
            "printf 'PERSISTENCE-%s\\n' OK; halt",
            "PERSISTENCE-OK", logs / "second-boot.log",
        )


if __name__ == "__main__":
    main()
