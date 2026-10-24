from pathlib import Path
import tempfile
import unittest

from tools.export_samples import export_samples, property_map, safe_name


class SampleExportTests(unittest.TestCase):
    def test_safe_output_names(self):
        self.assertEqual(safe_name("School_menu_bench2"), "School_menu_bench2")
        for value in ("../outside", "a/b", "a\\b", "a\nnewmtl", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                safe_name(value)

    def test_old_material_property_keys(self):
        self.assertEqual(property_map([({"name": "_Color"}, 1), ("_MainTex", 2)]),
                         {"_Color": 1, "_MainTex": 2})

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            original = path / "existing.obj"
            original.write_bytes(b"keep")
            with self.assertRaises(FileExistsError):
                export_samples(path)
            self.assertEqual(original.read_bytes(), b"keep")


if __name__ == "__main__":
    unittest.main()
