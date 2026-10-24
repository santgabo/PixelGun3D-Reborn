from pathlib import Path, PurePosixPath
import hashlib
import json
import math
import tempfile
import unittest

from tools.export_bulk import (
    EXPORTER_REVISION, Journal, ROOT, build_obj, check_obj_text, choose_renderer, decide,
    inside, item_relative_path, ordered_groups, prepare_output, relative_reference, trial_subset,
)


def record(status, output_json, error=None, revision=EXPORTER_REVISION):
    return {"kind": "audio", "file_id": 1, "path_id": 1, "archive": "obb",
            "logical_path": "assets/bin/Data/clip.assets", "name": "bell", "status": status,
            "output_json": output_json, "detail_json": json.dumps({"exporter_revision": revision}),
            "error": error, "updated_at": "t"}


class BulkLayoutTests(unittest.TestCase):
    def test_duplicate_and_unsafe_names_do_not_share_a_path(self):
        first = item_relative_path("texture", "obb", "assets/bin/Data/a.assets", 1, "Light", ".png")
        second = item_relative_path("texture", "obb", "assets/bin/Data/b.assets", 1, "Light", ".png")
        third = item_relative_path("texture", "obb", "assets/bin/Data/a.assets", 2, "Light", ".png")
        weapon = item_relative_path("texture", "obb", "assets/bin/Data/map.assets", 1, "PixelGun_2.0_map", ".png")
        messy = item_relative_path("mesh", "apk", "assets/bin/Data/level.assets", -12,
                                   "Combined Mesh (root: scene)", ".obj")
        self.assertEqual(len({first, second, third}), 3)
        self.assertEqual(weapon.name, "1_PixelGun_2.0_map.png")
        self.assertEqual(messy.name, "-12_Combined_Mesh_root_scene.obj")
        self.assertNotIn("..", messy.parts)
        for value in ("../outside", "assets/../x", "/abs", "a\\b", ""):
            with self.subTest(value=value), self.assertRaises(ValueError):
                item_relative_path("mesh", "obb", value, 1, "a", ".obj")
        with self.assertRaises(ValueError):
            item_relative_path("mesh", "../obb", "assets/a", 1, "a", ".obj")

    def test_obj_conversion_matches_unitypy_rules(self):
        vertices = [(1, 2, 3), (0, 1, 0), (-2, 0, 4)]
        uvs = [(0, 0), (1, 0), (0, 1)]
        normals = [(0, 1, 0), (0, 0, 1), (1, 0, 0)]
        triangles = [[(0, 1, 2)]]
        text, positions, uv_out, normal_out, info = build_obj(
            "bench", "bench.mtl", vertices, uvs, normals, triangles, ["atlas"])
        self.assertEqual(positions[0], (-1, 2, 3))
        self.assertEqual(normal_out[2], (-1, 0, 0))
        self.assertIn("\nf 3/3/3 2/2/2 1/1/1\n", text)
        self.assertIn("usemtl atlas", text)
        check_obj_text(text, positions, uv_out, normal_out, triangles)
        self.assertEqual(info["triangles"], 1)

        bare, _, _, _, bare_info = build_obj("bare", None, vertices, [], normals, triangles, [])
        self.assertNotIn("vt ", bare)
        self.assertIn("f 3//3 2//2 1//1", bare)
        self.assertFalse(bare_info["uv_exported"])
        replaced, *_rest, replaced_info = build_obj(
            "bad", None, [(math.nan, 0, 0)], [], [], [[(0, 0, 0)]], [])
        self.assertIn("v 0 0 0", replaced)
        self.assertGreater(replaced_info["non_finite_replaced"], 0)
        large = [(14172.634765625, -14121.634765625)] * 3
        text, positions, uv_out, normal_out, _info = build_obj(
            "lightmap", None, vertices, large, [], triangles, [])
        check_obj_text(text, positions, uv_out, normal_out, triangles)

    def test_texture_reference_stays_inside_the_output(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            mtl = output / "models" / "obb" / "a.assets" / "1_bench.mtl"
            png = output / "textures" / "apk" / "b.assets" / "2_map.png"
            mtl.parent.mkdir(parents=True)
            png.parent.mkdir(parents=True)
            reference = relative_reference(mtl, png)
            self.assertFalse(PurePosixPath(reference).is_absolute())
            resolved = (mtl.parent / reference).resolve()
            self.assertEqual(resolved, png.resolve())
            self.assertTrue(inside(output, resolved))

    def test_resume_skips_verified_files_and_retries_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            journal = Journal(output / "journal.sqlite")
            relative = "audio/obb/assets/bin/Data/clip.assets/1_bell.wav"
            path = output / relative
            path.parent.mkdir(parents=True)
            payload = b"RIFFxxxx"
            path.write_bytes(payload)
            digest = hashlib.sha256(payload).hexdigest()
            outputs = json.dumps([{"path": relative, "sha256": digest, "size_bytes": len(payload)}])
            journal.put(record("ok", outputs))
            self.assertEqual(decide(journal.get("audio", 1, 1), output), "skip")
            path.write_bytes(b"changed!")
            self.assertEqual(decide(journal.get("audio", 1, 1), output), "export")
            journal.put(record("failed", "[]", "boom"))
            self.assertEqual(decide(journal.get("audio", 1, 1), output), "export")
            journal.put(record("skipped", "[]", "malla sin vértices"))
            self.assertEqual(decide(journal.get("audio", 1, 1), output), "skip")
            journal.put(record("ok", outputs, revision=EXPORTER_REVISION - 1))
            path.write_bytes(payload)
            self.assertEqual(decide(journal.get("audio", 1, 1), output), "export")
            self.assertIsNone(journal.get("audio", 1, 2))
            journal.close()

    def test_existing_output_without_a_journal_is_refused(self):
        with self.assertRaises(ValueError):
            prepare_output(Path("/tmp/pixelgun-bulk-outside"))
        with self.assertRaises(ValueError):
            prepare_output(ROOT / "exports" / "samples")
        with tempfile.TemporaryDirectory(dir=ROOT / "exports") as directory:
            path = Path(directory)
            (path / "note.txt").write_text("keep")
            with self.assertRaises(FileExistsError):
                prepare_output(path)
            self.assertEqual((path / "note.txt").read_text(), "keep")

    def test_renderer_choice_is_stable(self):
        same = {"index": 0, "resolution": "resolved", "target_file": 5, "target_path_id": 9}
        other = {"index": 0, "resolution": "resolved", "target_file": 2, "target_path_id": 2}
        chosen, status = choose_renderer([
            {"file_id": 2, "path_id": 1, "slots": [same]},
            {"file_id": 1, "path_id": 8, "slots": [dict(same)]},
        ], mesh_file_id=1)
        self.assertEqual(status, "unique")
        self.assertEqual(chosen["file_id"], 1)
        chosen, status = choose_renderer([
            {"file_id": 4, "path_id": 2, "slots": [same]},
            {"file_id": 4, "path_id": 1, "slots": [other]},
        ], mesh_file_id=9)
        self.assertEqual(status, "ambiguous")
        self.assertEqual(chosen["path_id"], 1)
        self.assertEqual(choose_renderer([], 1), (None, "missing"))
        matching = {"file_id": 9, "path_id": 2, "slots": [same]}
        other_user = {"file_id": 9, "path_id": 3, "slots": [dict(same)]}
        shorter = {"file_id": 1, "path_id": 1, "slots": [same, other]}
        ordered = ordered_groups([shorter, matching, other_user], mesh_file_id=8, submesh_count=1)
        self.assertEqual(len(ordered), 2)
        self.assertEqual({renderer["path_id"] for renderer in ordered[0]}, {2, 3})

    def test_trial_keeps_known_samples_and_distinct_duplicates(self):
        rows = []

        def add(kind, archive, logical, name, file_id, path_id, details="{}"):
            rows.append({"kind": kind, "archive": archive, "logical_path": logical, "name": name,
                         "file_id": file_id, "path_id": path_id, "details_json": details,
                         "type": kind, "sha256": "abc"})

        add("mesh", "obb", "assets/bin/Data/sharedassets104.assets", "School_menu_bench2", 1, 34)
        add("texture", "obb", "assets/bin/Data/sharedassets104.assets", "school_menu_atlas", 1, 17)
        add("audio", "obb", "assets/bin/Data/sharedassets104.assets", "Bells_lobby", 1, 41)
        add("mesh", "obb", "assets/bin/Data/47f34ace77a313c4e9cbfa48107beff5", "PixlGun_Mesh", 2, 4)
        add("texture", "obb", "assets/bin/Data/bb9c08d0a2b036641874e7977d1b5c66", "PixelGun_2.0_map", 3, 1)
        add("audio", "obb", "assets/bin/Data/bbf7b2eeb07f36447b71815024142b60", "PixlGun_Shoot", 4, 1)
        add("texture", "obb", "assets/bin/Data/empty.assets", "Font Texture", 5, 1,
            '{"m_Width": 0, "m_Height": 0}')
        add("mesh", "obb", "assets/bin/Data/empty.assets", "Empty", 5, 2, '{"vertex_count": 0}')
        add("mesh", "obb", "assets/bin/Data/gun.assets", "Glock_Mesh", 6, 1,
            '{"vertex_count": 10, "submesh_count": 2}')
        add("texture", "apk", "assets/bin/Data/a.assets", "Enemy11", 7, 1,
            '{"m_Width": 32, "m_Height": 32, "m_TextureFormat": 3}')
        add("texture", "obb", "assets/bin/Data/b.assets", "Enemy11", 8, 1,
            '{"m_Width": 32, "m_Height": 32, "m_TextureFormat": 3}')
        add("sprite", "obb", "assets/bin/Data/ui.assets", "Background", 9, 1)
        chosen = trial_subset(rows)
        identities = {(row["kind"], row["name"], row["file_id"], row["path_id"]) for row in chosen}
        self.assertIn(("mesh", "School_menu_bench2", 1, 34), identities)
        self.assertIn(("audio", "PixlGun_Shoot", 4, 1), identities)
        self.assertIn(("mesh", "Empty", 5, 2), identities)
        self.assertEqual(sum(row["name"] == "Enemy11" for row in chosen), 2)
        paths = {item_relative_path(row["kind"], row["archive"], row["logical_path"], row["path_id"],
                                    row["name"], ".png")
                 for row in chosen if row["name"] == "Enemy11"}
        self.assertEqual(len(paths), 2)


if __name__ == "__main__":
    unittest.main()
