import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "tools/bitbake"


@unittest.skipUnless((ENGINE / "bin/bitbake").is_file(), "run scripts/bootstrap first")
class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="bitbaker-metadata-")
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name)
        for directory in ("meta-core", "meta-bsp", "meta-distro", "build/conf"):
            shutil.copytree(ROOT / directory, self.project / directory)
        (self.project / "scripts").mkdir()
        shutil.copy2(ROOT / "scripts/bb", self.project / "scripts/bb")
        shutil.copy2(ROOT / "scripts/make-image.py", self.project / "scripts/make-image.py")
        (self.project / "tools").mkdir()
        (self.project / "tools/bitbake").symlink_to(ENGINE)
        self.env = os.environ.copy()
        for name in ("BBPATH", "BBFILES", "BBLAYERS", "BUILDDIR",
                     "BB_ENV_PASSTHROUGH_ADDITIONS"):
            self.env.pop(name, None)

    def bb(self, *args, env=None):
        result = subprocess.run(
            [str(self.project / "scripts/bb"), *args],
            cwd=self.project, env=self.env if env is None else env,
            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stdout)
        return result.stdout

    def test_ambient_environment_does_not_rebuild_but_recipe_edit_does(self):
        self.bb("hello")
        stamps = self.project / "build/tmp/stamps/versatilepb"
        before = next(stamps.glob("hello-1.0-r0.do_greet.sigdata.*"))
        log = self.project / "build/tmp/work/versatilepb/hello-1.0-r0/temp/log.do_greet"
        original_log = log.resolve()
        empty = self.project / "empty-bin"
        empty.mkdir()
        home = self.project / "home"
        home.mkdir()
        changed_env = self.env | {
            "PATH": str(empty) + ":" + self.env["PATH"],
            "HOME": str(home), "USER": "student", "LOGNAME": "student",
            "PWD": str(home), "SHELL": "/bin/sh",
        }
        output = self.bb("hello", env=changed_env)
        self.assertIn("2 didn't need to be rerun", output)
        self.assertEqual(log.resolve(), original_log)

        recipe = self.project / "meta-core/recipes-demo/hello/hello_1.0.bb"
        recipe.write_text(recipe.read_text().replace(
            "Hello from standalone BitBake!", "Hello from my edited recipe!"
        ))
        self.bb("hello", env=changed_env)
        self.assertNotEqual(log.resolve(), original_log)
        self.assertIn("Hello from my edited recipe!", log.read_text())
        after = next(path for path in stamps.glob("hello-1.0-r0.do_greet.sigdata.*")
                     if path != before)
        dumps = [
            subprocess.run(
                [str(ENGINE / "bin/bitbake-dumpsig"), str(path)],
                check=True, text=True, capture_output=True, timeout=30,
            ).stdout
            for path in (before, after)
        ]
        self.assertIn("Hello from standalone BitBake!", dumps[0])
        self.assertIn("Hello from my edited recipe!", dumps[1])
        self.assertNotEqual(dumps[0], dumps[1])

    @unittest.skipUnless(shutil.which("arm-linux-gnueabi-gcc"), "cross compiler required")
    def test_optional_program_is_staged_and_selected_by_local_configuration(self):
        self.assertIn('IMAGE_INSTALL="busybox base-files"', self.bb("-e", "simple-image"))
        recipe = self.project / "meta-core/recipes-demo/hello-arm/hello-arm_1.0.bb"
        recipe.write_text(recipe.read_text().replace("inherit build", "inherit component"))
        local = self.project / "build/conf/local.conf"
        local.write_text(local.read_text() + '\nIMAGE_INSTALL = "busybox base-files hello-arm"\n')
        self.assertIn(
            'IMAGE_INSTALL="busybox base-files hello-arm"', self.bb("-e", "simple-image")
        )
        self.bb("hello-arm")
        installed = self.project / "build/tmp/work/versatilepb/hello-arm-1.0-r0/image/usr/bin/hello-arm"
        staged = self.project / "build/tmp/components/versatilepb/hello-arm/usr/bin/hello-arm"
        self.assertEqual(installed.read_bytes(), staged.read_bytes())
        self.bb("-g", "simple-image")
        graph = (self.project / "build/task-depends.dot").read_text()
        self.assertIn('"simple-image.do_rootfs" -> "hello-arm.do_stage"', graph)

    def test_reconstruction_parses_before_and_after_kernel_checkpoint(self):
        text = (ROOT / "TUTORIAL.md").read_text()
        reconstruction = self.project / "reconstruction"
        for filename, content in re.findall(
            r"\*\*`([^`]+)`\*\*\n\n```bitbake\n(.*?)\n```", text, re.S
        ):
            if filename == "meta-core/classes/build.bbclass":
                continue
            destination = reconstruction / filename
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content + "\n")
        recipe_name, recipe = re.search(
            r"\*\*Chapter 5 checkpoint: `([^`]+)`\*\*\n\n```bitbake\n(.*?)\n```",
            text, re.S,
        ).groups()
        destination = reconstruction / recipe_name
        destination.parent.mkdir(parents=True)
        destination.write_text(recipe + "\n")
        fragment = "meta-bsp/recipes-kernel/linux/files/versatilepb.cfg"
        (reconstruction / fragment).parent.mkdir()
        shutil.copy2(ROOT / fragment, reconstruction / fragment)
        shutil.copytree(self.project / "scripts", reconstruction / "scripts")
        (reconstruction / "tools").mkdir()
        (reconstruction / "tools/bitbake").symlink_to(ENGINE)
        self.project = reconstruction
        self.bb("hello")
        output = self.bb("-c", "listtasks", "linux")
        self.assertIn("do_unpack", output)
        self.assertNotIn("do_compile", output)
        for filename in (
            "meta-core/classes/build.bbclass", "meta-core/classes/deploy.bbclass",
            "meta-bsp/recipes-kernel/linux/files/qemu-versatile-pb.dts", recipe_name,
        ):
            shutil.copy2(ROOT / filename, reconstruction / filename)
        output = self.bb("-c", "listtasks", "linux")
        self.assertIn("do_compile", output)
        self.assertIn("do_devicetree", output)


if __name__ == "__main__":
    unittest.main()
