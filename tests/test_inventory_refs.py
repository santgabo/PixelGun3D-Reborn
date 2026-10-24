import unittest

from tools.inventory_refs import FileIndex, pointers, stream_descriptors


def file(key, path, archive="obb"):
    return {"id": key, "logical_path": "assets/bin/Data/" + path, "archive": archive}


class ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.index = FileIndex([
            file(1, "level0", "apk"), file(2, "sharedassets1.assets"),
            file(3, "Resources/unity_builtin_extra", "apk"),
            file(4, "unity default resources", "apk"),
            file(5, "folder/a.resource"), file(6, "other/a.resource"),
        ])

    def test_cross_archive_reference(self):
        self.assertEqual(self.index.resolve(1, "sharedassets1.assets")[:2], (2, "path_suffix"))

    def test_engine_alias_and_case(self):
        self.assertEqual(self.index.resolve(2, "resources/UNITY_BUILTIN_EXTRA")[0], 3)
        self.assertEqual(self.index.resolve(2, "library/unity default resources")[:2], (4, "basename"))

    def test_missing_and_ambiguous(self):
        self.assertEqual(self.index.resolve(1, "missing")[1], "missing")
        self.assertEqual(self.index.resolve(1, "archive:/unknown/a.resource")[1], "ambiguous")
        self.assertEqual(self.index.resolve(1, "")[1], "missing")

    def test_qualified_path(self):
        self.assertEqual(self.index.resolve(1, "folder/a.resource")[0], 5)

    def test_same_path_in_other_archive_is_not_overwritten(self):
        index = FileIndex([file(1, "level0", "apk"), file(2, "level0", "obb")])
        self.assertEqual(index.resolve(1, "level0")[0], 1)
        self.assertEqual(index.resolve(2, "level0")[0], 2)

    def test_pointer_walker(self):
        data = {"textures": [("main", {"ptr": {"m_FileID": 2, "m_PathID": 16}})], "bytes": b"ignore"}
        self.assertEqual(list(pointers(data)), [("textures[0][1].ptr", 2, 16)])

    def test_stream_fields(self):
        texture = {"m_StreamData": {"path": "image.resS", "offset": 12, "size": 30}}
        audio = {"m_Resource": {"m_Source": "audio.resource", "m_Offset": 2**33, "m_Size": 100}}
        self.assertEqual(list(stream_descriptors(texture)), [("m_StreamData", "image.resS", 12, 30)])
        self.assertEqual(list(stream_descriptors(audio)), [("m_Resource", "audio.resource", 2**33, 100)])
        self.assertEqual(list(stream_descriptors({"m_StreamData": {"path": "", "size": 0}})), [])
        self.assertEqual(list(stream_descriptors({"m_VertexData": {"m_Streams": []}})), [])


if __name__ == "__main__":
    unittest.main()
