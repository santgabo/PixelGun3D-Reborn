from array import array
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from tools.export_gltf import (
    ConversionError, NEAREST, accessor_values, convert_obj, destination, export_gltf, parse_obj,
    prepare_output, read_glb, verify,
)

PNG = b"\x89PNG\r\n\x1a\n" + b"not really an image"


class Fixture:
    """exports/bulk/{models,textures} falsos dentro de un directorio temporal."""

    def __init__(self, test):
        directory = tempfile.TemporaryDirectory()
        test.addCleanup(directory.cleanup)
        self.root = Path(directory.name).resolve()
        self.exports = self.root / "exports"
        self.models = self.exports / "bulk/models/obb/assets"
        self.textures = self.exports / "bulk/textures/obb/assets"
        self.models.mkdir(parents=True)
        self.textures.mkdir(parents=True)
        self.png = self.textures / "1_atlas.png"
        self.png.write_bytes(PNG)

    def write(self, name, obj, mtl=None):
        (self.models / f"{name}.obj").write_text(obj.replace("MTL", f"{name}.mtl"))
        if mtl is not None:
            (self.models / f"{name}.mtl").write_text(mtl)
        return self.models / f"{name}.obj"

    def convert(self, name, filter_modes=None):
        obj = self.models / f"{name}.obj"
        glb = destination(self.exports / "bulk/models", self.exports / "gltf", obj)
        return convert_obj(obj, glb, self.exports, filter_modes or {}) + (glb,)


QUAD_OBJ = """g quad
mtllib MTL
v -1 0 0
v 1 0 0
v 1 2 0
v -1 2 0
vt 0 0
vt 1 0
vt 1 0.25
vt 0 0.25
vn 0 0 1
vn 0 0 1
vn 0 0 1
vn 0 0 1
g quad_0
usemtl atlas
f 1/1/1 2/2/2 3/3/3
g quad_1
usemtl flat
f 1/1/1 3/3/3 4/4/4
"""
MTL = """# test
newmtl atlas
Ka 0 0 0
Kd 0.5 0.25 1
Ks 0 0 0
d 1
illum 1
map_Kd {options}../../../textures/obb/assets/1_atlas.png
newmtl flat
Ka 0 0 0
Kd 1 1 1
Ks 0 0 0
d 0.5
illum 1
"""


class ConversionTests(unittest.TestCase):
    def test_glb_round_trip_keeps_geometry_and_leaves_the_png_alone(self):
        fixture = Fixture(self)
        fixture.write("quad", QUAD_OBJ, MTL.format(options=""))
        digest = hashlib.sha256(PNG).hexdigest()
        data, detail, glb = fixture.convert("quad", {"bulk/textures/obb/assets/1_atlas.png": 0})
        glb.parent.mkdir(parents=True)
        glb.write_bytes(data)
        document, binary = read_glb(glb)
        positions, uvs, normals, groups = parse_obj(fixture.models / "quad.obj")

        primitives = document["meshes"][0]["primitives"]
        self.assertEqual(len(primitives), 2)
        attributes = primitives[0]["attributes"]
        self.assertEqual(accessor_values(document, binary, attributes["POSITION"]), positions)
        self.assertEqual(accessor_values(document, binary, attributes["NORMAL"]), normals)
        self.assertEqual(detail["normals_renormalized"], 0)
        flipped = accessor_values(document, binary, attributes["TEXCOORD_0"])
        self.assertEqual(list(flipped[0::2]), list(uvs[0::2]))
        self.assertEqual(list(flipped[1::2]), [1.0 - value for value in uvs[1::2]])
        for primitive, (_, indices) in zip(primitives, groups):
            self.assertEqual(list(accessor_values(document, binary, primitive["indices"])), list(indices))
        position = document["accessors"][attributes["POSITION"]]
        self.assertEqual((position["min"], position["max"]), ([-1, 0, 0], [1, 2, 0]))
        self.assertEqual(detail["index_type"], "uint16")

        self.assertEqual(len(data) % 4, 0)
        for view in document["bufferViews"]:
            self.assertEqual(view["byteOffset"] % 4, 0)
        self.assertEqual(document["buffers"][0]["byteLength"], len(binary))

        atlas, flat = document["materials"]
        self.assertEqual(atlas["pbrMetallicRoughness"]["baseColorFactor"], [0.5, 0.25, 1.0, 1.0])
        self.assertNotIn("alphaMode", atlas)
        self.assertEqual(flat["alphaMode"], "BLEND")
        self.assertNotIn("baseColorTexture", flat["pbrMetallicRoughness"])
        uri = document["images"][0]["uri"]
        self.assertEqual((glb.parent / uri).resolve(), fixture.png.resolve())
        self.assertEqual(document["samplers"][0]["magFilter"], NEAREST)
        self.assertEqual(hashlib.sha256(fixture.png.read_bytes()).hexdigest(), digest)
        self.assertNotIn("extensionsUsed", document)

    def test_uv_scale_and_offset_become_a_texture_transform_in_gltf_v(self):
        fixture = Fixture(self)
        fixture.write("quad", QUAD_OBJ, MTL.format(options="-s 2 3 1 -o 0.5 0.25 0 "))
        data, detail, glb = fixture.convert("quad")
        glb.parent.mkdir(parents=True)
        glb.write_bytes(data)
        document, _ = read_glb(glb)
        transform = document["materials"][0]["pbrMetallicRoughness"]["baseColorTexture"]["extensions"]
        self.assertEqual(transform["KHR_texture_transform"], {"scale": [2, 3], "offset": [0.5, 1 - 3 - 0.25]})
        self.assertIn("KHR_texture_transform", document["extensionsUsed"])
        self.assertEqual(document["samplers"][0]["magFilter"], 9729)
        self.assertEqual(detail["uv_transform"], 1)

    def test_missing_uv_and_normals_leave_out_those_attributes_and_the_texture(self):
        fixture = Fixture(self)
        obj = "g t\nmtllib MTL\nv 0 0 0\nv 1 0 0\nv 0 1 0\ng t_0\nusemtl atlas\nf 1 2 3\n"
        fixture.write("bare", obj, MTL.format(options=""))
        data, detail, glb = fixture.convert("bare")
        glb.parent.mkdir(parents=True)
        glb.write_bytes(data)
        document, _ = read_glb(glb)
        self.assertEqual(list(document["meshes"][0]["primitives"][0]["attributes"]), ["POSITION"])
        self.assertNotIn("images", document)
        self.assertEqual(detail["ignored_textures"], 1)

        only_uv = "g t\nmtllib MTL\nv 0 0 0\nv 1 0 0\nv 0 1 0\nvt 0 0\nvt 1 0\nvt 0 1\ng t_0\nusemtl atlas\nf 1/1 2/2 3/3\n"
        fixture.write("uvonly", only_uv, MTL.format(options=""))
        _, detail, _ = fixture.convert("uvonly")
        self.assertTrue(detail["uv"])
        self.assertFalse(detail["normals"])

    def test_off_unit_normals_are_renormalized_and_the_rest_left_alone(self):
        fixture = Fixture(self)
        obj = ("g t\nmtllib MTL\nv 0 0 0\nv 1 0 0\nv 0 1 0\nvn 0 0 0.99\nvn 0 0 1\nvn 0 0 0\n"
               "g t_0\nf 1//1 2//2 3//3\n")
        fixture.write("soft", obj, "")
        data, detail, glb = fixture.convert("soft")
        glb.parent.mkdir(parents=True)
        glb.write_bytes(data)
        document, binary = read_glb(glb)
        values = accessor_values(document, binary, document["meshes"][0]["primitives"][0]["attributes"]["NORMAL"])
        self.assertEqual(list(values), [0, 0, 1, 0, 0, 1, 0, 0, 0])
        self.assertEqual(detail["normals_renormalized"], 1)

    def test_large_mesh_uses_uint32_indices(self):
        fixture = Fixture(self)
        count = 65536
        lines = ["g big"] + ["v 0 0 0"] * count + ["g big_0", f"f 1 2 {count}"]
        fixture.write("big", "\n".join(lines) + "\n")
        data, detail, glb = fixture.convert("big")
        glb.parent.mkdir(parents=True)
        glb.write_bytes(data)
        document, binary = read_glb(glb)
        primitive = document["meshes"][0]["primitives"][0]
        self.assertEqual(detail["index_type"], "uint32")
        self.assertEqual(list(accessor_values(document, binary, primitive["indices"])), [0, 1, count - 1])
        self.assertNotIn("materials", document)

    def test_rejects_what_the_extraction_never_writes(self):
        fixture = Fixture(self)
        head = "g t\nmtllib MTL\nv 0 0 0\nv 1 0 0\nv 0 1 0\nv 1 1 0\nvt 0 0\nvt 1 0\nvt 0 1\nvt 1 1\n"
        cases = {
            "quad": head + "g t_0\nf 1/1 2/2 3/3 4/4\n",
            "split": head + "g t_0\nf 1/1 2/3 3/2\n",
            "range": head + "g t_0\nf 1/1 2/2 9/3\n",
            "empty": head,
            "short_uv": head + "vt 0 0\ng t_0\nf 1/1 2/2 3/3\n",
            "unknown": head + "g t_0\nusemtl nowhere\nf 1/1 2/2 3/3\n",
            "directive": head + "curv 0 1 1 2\n",
        }
        for name, obj in cases.items():
            fixture.write(name, obj, MTL.format(options=""))
            with self.subTest(name), self.assertRaises(ConversionError):
                fixture.convert(name)

    def test_rejects_a_texture_path_that_leaves_exports(self):
        fixture = Fixture(self)
        outside = fixture.root / "secret.png"
        outside.write_bytes(PNG)
        obj = "g t\nmtllib MTL\nv 0 0 0\nv 1 0 0\nv 0 1 0\nvt 0 0\nvt 1 0\nvt 0 1\ng t_0\nusemtl atlas\nf 1/1 2/2 3/3\n"
        fixture.write("escape", obj, MTL.format(options="").replace("../../../textures/obb/assets/1_atlas.png", "../../../../../secret.png"))
        with self.assertRaises(ConversionError):
            fixture.convert("escape")
        fixture.write("ghost", obj, MTL.format(options="").replace("1_atlas.png", "9_ghost.png"))
        with self.assertRaises(ConversionError):
            fixture.convert("ghost")


class BatchTests(unittest.TestCase):
    def test_bad_obj_is_recorded_and_the_rest_is_written_then_resumed(self):
        fixture = Fixture(self)
        fixture.write("good", QUAD_OBJ, MTL.format(options=""))
        fixture.write("bad", "g bad\nv 0 0 0\nf 1 1\n")
        output = fixture.exports / "gltf"
        source = fixture.exports / "bulk"

        first = export_gltf(output, source, workers=2, root=fixture.root)
        self.assertEqual((first["ok"], first["failed"], first["skipped"]), (1, 1, 0))
        self.assertTrue((output / "obb/assets/good.glb").is_file())
        self.assertFalse((output / "obb/assets/bad.glb").exists())
        rows = {row[0]: row for row in sqlite3.connect(output / "journal.sqlite").execute(
            "SELECT obj_path, status, glb_sha256, error FROM models")}
        self.assertEqual(rows["obb/assets/bad.obj"][1], "failed")
        self.assertIn("triángulo", rows["obb/assets/bad.obj"][3])
        self.assertEqual(rows["obb/assets/good.obj"][2],
                         hashlib.sha256((output / "obb/assets/good.glb").read_bytes()).hexdigest())

        second = export_gltf(output, source, workers=2, root=fixture.root)
        self.assertEqual((second["ok"], second["failed"], second["skipped"]), (0, 1, 1))

        again = export_gltf(output, source, workers=2, root=fixture.root)
        self.assertEqual((again["ok"], again["skipped"]), (0, 1))

        (output / "obb/assets/good.glb").write_bytes(b"corrupt")
        third = export_gltf(output, source, workers=2, root=fixture.root)
        self.assertEqual((third["ok"], third["skipped"]), (1, 0))
        document, _ = read_glb(output / "obb/assets/good.glb")
        self.assertEqual(len(document["meshes"][0]["primitives"]), 2)

        fixture.write("bad", QUAD_OBJ, MTL.format(options=""))
        (fixture.models / "bad.mtl").write_text(MTL.format(options=""))
        fourth = export_gltf(output, source, workers=2, root=fixture.root)
        self.assertEqual((fourth["ok"], fourth["failed"], fourth["skipped"]), (1, 0, 1))
        self.assertEqual(fourth["verify"]["glb_missing"], [])
        self.assertEqual(fourth["verify"]["textures_missing"], [])

    def test_verify_reports_missing_glb_partials_and_textures(self):
        fixture = Fixture(self)
        fixture.write("good", QUAD_OBJ, MTL.format(options=""))
        output = fixture.exports / "gltf"
        export_gltf(output, fixture.exports / "bulk", workers=1, root=fixture.root)
        (output / "stray.glb.partial").write_bytes(b"x")
        fixture.png.unlink()
        check = verify(output, fixture.exports / "bulk/models", fixture.exports)
        self.assertEqual(len(check["partials"]), 1)
        self.assertEqual(len(check["textures_missing"]), 1)

    def test_protected_and_mixed_destinations_are_refused(self):
        fixture = Fixture(self)
        for reserved in ("exports/bulk", "exports/samples", "exports/samples-weapon", "exports", "exports/bulk/gltf"):
            with self.subTest(reserved), self.assertRaises(ValueError):
                prepare_output(fixture.root / reserved, fixture.root)
        with self.assertRaises(ValueError):
            prepare_output(fixture.root.parent / "elsewhere", fixture.root)
        occupied = fixture.exports / "occupied"
        occupied.mkdir()
        (occupied / "file.txt").write_text("x")
        with self.assertRaises(FileExistsError):
            prepare_output(occupied, fixture.root)
        self.assertEqual(json.loads("{}"), {})


if __name__ == "__main__":
    unittest.main()
