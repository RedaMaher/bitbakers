import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "make-image.py"
SPEC = importlib.util.spec_from_file_location("make_image", SCRIPT)
image_builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(image_builder)
os.environ["PATH"] += ":/usr/sbin:/sbin"


class ImageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "root"
        self.root.mkdir()
        self.output = Path(self.temp.name) / "rootfs.ext2"

    def test_rejects_invalid_sd_sizes(self):
        for size in (0, -1, 4096, 12000, 65535):
            with self.subTest(size=size), self.assertRaises(ValueError):
                image_builder.make_image(self.root, self.output, size, "test")
        self.assertFalse(self.output.exists())

    def test_rejects_missing_root(self):
        with self.assertRaises(ValueError):
            image_builder.make_image(self.root / "absent", self.output, 8192, "test")

    def test_rejects_debugfs_command_characters(self):
        (self.root / 'bad"name').touch()
        with self.assertRaises(ValueError):
            image_builder.make_image(self.root, self.output, 8192, "test")
        self.assertFalse(self.output.exists())

    def test_rejects_long_label(self):
        with self.assertRaises(ValueError):
            image_builder.make_image(self.root, self.output, 8192, "x" * 17)

    @unittest.skipUnless(
        all(shutil.which(tool) for tool in ("mke2fs", "debugfs", "e2fsck")),
        "e2fsprogs required",
    )
    def test_real_image_contents_permissions_ownership_and_replacement(self):
        (self.root / "etc").mkdir()
        (self.root / "etc" / "message").write_text("hello\n")
        (self.root / "etc" / "a space").write_text("quoted path\n")
        (self.root / "tmp").mkdir(mode=0o1777)
        (self.root / "tmp").chmod(0o1777)
        (self.root / "sbin").mkdir()
        (self.root / "sbin" / "init").symlink_to("../bin/busybox")
        image_builder.make_image(self.root, self.output, 8192, "test")
        self.assertEqual(self.output.stat().st_size, 8192 * 1024)

        def debugfs(command):
            return subprocess.run(
                ["debugfs", "-R", command, str(self.output)],
                check=True, text=True, capture_output=True,
            ).stdout

        self.assertEqual(debugfs("cat /etc/message"), "hello\n")
        for path in ("/", "/etc/message", '"/etc/a space"', "/sbin/init"):
            stat = debugfs(f"stat {path}")
            self.assertRegex(stat, r"User:\s+0\s+Group:\s+0")
        self.assertIn("1777", debugfs("stat /tmp"))
        self.assertIn("../bin/busybox", debugfs("stat /sbin/init"))
        (self.root / "etc" / "message").write_text("rebuilt\n")
        image_builder.make_image(self.root, self.output, 8192, "test")
        self.assertEqual(debugfs("cat /etc/message"), "rebuilt\n")


if __name__ == "__main__":
    unittest.main()
