from importlib import metadata
from pathlib import Path
import platform
import re
import sys
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]


def normalized(name):
    return re.sub(r"[-_.]+", "-", name).lower()


class UvProjectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project = tomllib.loads((ROOT / "pyproject.toml").read_text())
        cls.lock = tomllib.loads((ROOT / "uv.lock").read_text())

    def test_native_uv_project_and_direct_dependencies(self):
        self.assertFalse(self.project["tool"]["uv"]["package"])
        self.assertEqual(self.project["project"]["requires-python"], ">=3.12,<3.13")
        dependencies = self.project["project"]["dependencies"]
        self.assertIn("unitypy==1.25.4", dependencies)
        self.assertIn("pillow==13.0.0", dependencies)
        self.assertTrue((ROOT / self.project["project"]["readme"]).is_file())

    def test_interpreter_matches_uv_pin(self):
        self.assertEqual(platform.python_version(), (ROOT / ".python-version").read_text().strip())
        self.assertNotEqual(sys.prefix, sys.base_prefix)

    def test_installed_versions_are_in_uv_lock(self):
        locked = {}
        for package in self.lock["package"]:
            if "registry" in package["source"]:
                locked.setdefault(package["name"], set()).add(package["version"])
        for dist in metadata.distributions():
            with self.subTest(package=dist.metadata["Name"]):
                self.assertIn(dist.version, locked.get(normalized(dist.metadata["Name"]), set()))
        self.assertFalse((ROOT / "requirements-extraction.in").exists())
        self.assertFalse((ROOT / "requirements-extraction.txt").exists())


if __name__ == "__main__":
    unittest.main()
