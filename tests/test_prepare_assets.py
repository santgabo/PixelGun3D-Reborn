import hashlib
from pathlib import Path
import stat
import tempfile
import unittest
from zipfile import ZipFile, ZipInfo

from tools.prepare_assets import member_groups, prepare_archive

PREFIX = "assets/bin/Data/"


class PreparationTests(unittest.TestCase):
    def test_numeric_split_order(self):
        infos = [ZipInfo(f"{PREFIX}mesh.split{i}") for i in [0, 1, 10, 11, 2, 3, 4, 5, 6, 7, 8, 9]]
        parts = member_groups(infos)[PREFIX + "mesh"]
        self.assertEqual([part.filename for part in parts],
                         [f"{PREFIX}mesh.split{i}" for i in range(12)])

    def test_invalid_groups(self):
        for names in [
            ["mesh.split1"], ["mesh.split0", "mesh.split2"],
            ["mesh", "mesh.split0"], ["mesh.split0", "mesh.split00"],
            ["mesh", "mesh"], ["../../outside"], ["folder\\outside"],
            ["folder//mesh"], ["folder/./mesh"], [".split0"],
        ]:
            with self.subTest(names=names), self.assertRaises(ValueError):
                member_groups([ZipInfo(PREFIX + name) for name in names])

    def test_symlink_rejected(self):
        info = ZipInfo(PREFIX + "link")
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        with self.assertRaises(ValueError):
            member_groups([info])

    def test_non_data_not_prepared(self):
        self.assertEqual(member_groups([ZipInfo("classes.dex")]), {})

    def test_prepared_content_and_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive_path = root / "input.zip"
            with ZipFile(archive_path, "w") as archive:
                archive.writestr(PREFIX + "mesh.split1", b"second")
                archive.writestr(PREFIX + "mesh.split0", b"first")
                archive.writestr("classes.dex", b"not a Unity resource")
            rows, entries = prepare_archive("apk", archive_path, root / "prepared")
            self.assertEqual(len(rows), 1)
            self.assertEqual((root / "prepared" / rows[0]["prepared_path"]).read_bytes(), b"firstsecond")
            self.assertEqual(rows[0]["sha256"], hashlib.sha256(b"firstsecond").hexdigest())
            self.assertEqual(rows[0]["members"], [PREFIX + "mesh.split0", PREFIX + "mesh.split1"])
            self.assertFalse(entries[-1]["prepared"])
            # Una ruta igual en otro paquete conserva su propia procedencia.
            other, _ = prepare_archive("obb", archive_path, root / "prepared")
            self.assertNotEqual(rows[0]["prepared_path"], other[0]["prepared_path"])
            with self.assertRaises(FileExistsError):
                prepare_archive("apk", archive_path, root / "prepared")


if __name__ == "__main__":
    unittest.main()
