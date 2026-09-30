import os
from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
