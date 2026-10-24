from types import SimpleNamespace
import unittest

from tools.inventory_assets import create_database, inventory_object, resolve_links
from tools.inventory_refs import FileIndex


def file(key, name):
    return {"id": key, "archive": "obb", "logical_path": "assets/bin/Data/" + name,
            "prepared_path": "obb/" + name, "size_bytes": 100, "sha256": "test"}


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.files = [file(1, "mesh"), file(2, "texture"), file(3, "audio.resource")]
        self.db = create_database(":memory:", self.files)
        self.index = FileIndex(self.files)

    def tearDown(self):
        self.db.close()

    def object(self, file_id, path_id):
        self.db.execute("INSERT INTO objects VALUES(?,?,?,?,?,?,?,?,?)",
                        (file_id, path_id, 43, "Mesh", "test", "ok", 0, 10, "{}"))

    def link(self, file_id, path_id):
        self.db.execute("INSERT INTO links(owner_file,target_file_id,target_path_id) VALUES(1,?,?)",
                        (file_id, path_id))

    def test_pointer_resolution(self):
        self.object(1, 12)
        self.object(2, 16)
        self.db.execute("INSERT INTO externals VALUES(1,1,'texture',NULL,2,2,'path_suffix','[2]')")
        self.db.execute("INSERT INTO externals VALUES(1,2,'missing',NULL,2,NULL,'missing','[]')")
        for fid, pid in [(0, 12), (1, 16), (1, 99), (0, 0), (2, 16), (3, 16), (-1, 16)]:
            self.link(fid, pid)
        resolve_links(self.db)
        results = self.db.execute("SELECT resolution FROM links ORDER BY rowid").fetchall()
        self.assertEqual([row[0] for row in results],
                         ["resolved", "resolved", "missing_object", "null",
                          "unresolved_file", "invalid_file_id", "invalid_file_id"])

    def test_field_error_keeps_name_and_identity(self):
        def fail():
            raise ValueError("unsupported test fields")
        obj = SimpleNamespace(path_id=4, class_id=43, type=SimpleNamespace(name="Mesh"),
                              byte_start=0, byte_size=10, parse_as_dict=fail, peek_name=lambda: "mesh")
        self.assertEqual(inventory_object(self.db, self.index, 1, obj), 1)
        self.assertEqual(self.db.execute("SELECT name,name_status FROM objects").fetchone(), ("mesh", "ok"))
        self.assertEqual(self.db.execute("SELECT stage FROM errors").fetchone()[0], "object_fields")

    def test_stream_ranges_are_checked_without_decoder(self):
        data = {"m_Name": "sound", "m_Resource": {"m_Source": "audio.resource", "m_Offset": 90, "m_Size": 11}}
        obj = SimpleNamespace(path_id=4, class_id=83, type=SimpleNamespace(name="AudioClip"),
                              byte_start=0, byte_size=10, parse_as_dict=lambda: data)
        self.assertEqual(inventory_object(self.db, self.index, 1, obj), 0)
        self.assertEqual(self.db.execute("SELECT target_file,range_valid FROM streams").fetchone(), (3, 0))

    def test_resource_name_is_a_pointer_not_a_unique_identity(self):
        data = {"m_Container": [("same", {"m_FileID": 0, "m_PathID": 1}),
                                ("same", {"m_FileID": 1, "m_PathID": 2})]}
        obj = SimpleNamespace(path_id=4, class_id=147, type=SimpleNamespace(name="ResourceManager"),
                              byte_start=0, byte_size=10, parse_as_dict=lambda: data, peek_name=lambda: None)
        inventory_object(self.db, self.index, 1, obj)
        self.assertEqual(self.db.execute("SELECT count(*) FROM links WHERE logical_name='same'").fetchone()[0], 2)


if __name__ == "__main__":
    unittest.main()
