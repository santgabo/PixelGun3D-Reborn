"""Exporta solo los tres candidatos acordados; no es un exportador masivo.

Fuentes: https://github.com/K0lb3/UnityPy#important-object-types
MeshExporter refleja X e invierte el winding; no modifica las UV.
"""

import argparse
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
import math
from pathlib import Path
import re
import sqlite3
import tempfile

from PIL import Image
import UnityPy
from UnityPy.export.MeshExporter import export_mesh_obj
from UnityPy.helpers.MeshHelper import MeshHandler

from tools.prepare_assets import sha256_file
from tools.sample_checks import inspect_obj, inspect_wav

ROOT = Path(__file__).resolve().parents[1]


def checked_input(db, file_id):
    row = db.execute("SELECT * FROM files WHERE id=?", (file_id,)).fetchone()
    if row is None or row["status"] != "ok":
        raise ValueError(f"Archivo no validado en el catálogo: {file_id}")
    raw = (ROOT / "work/prepared" / row["prepared_path"]).read_bytes()
    if hashlib.sha256(raw).hexdigest() != row["sha256"]:
        raise ValueError(f"Copia preparada modificada: {row['prepared_path']}")
    return dict(row), raw


def safe_name(name):
    # Las muestras elegidas solo usan estos caracteres; no aceptar rutas del juego.
    if not re.fullmatch(r"[A-Za-z0-9_-]+", name):
        raise ValueError(f"Nombre no permitido para esta prueba: {name!r}")
    return name


def property_map(pairs):
    return {(key["name"] if isinstance(key, dict) else key): value for key, value in pairs}


def check_mesh_export(mesh, text):
    handler = MeshHandler(mesh)
    handler.process()
    parsed = inspect_obj(text)
    source = {"vertices": [(-v[0], v[1], v[2]) for v in handler.m_Vertices],
              "uv": [tuple(v[:2]) for v in handler.m_UV0],
              "normals": [(-v[0], v[1], v[2]) for v in handler.m_Normals]}
    for key, expected in source.items():
        actual = parsed[key]
        if len(expected) != len(actual):
            raise ValueError(f"Cantidad OBJ distinta del origen: {key}")
        for before, after in zip(expected, actual):
            if any(not math.isfinite(a) or abs(a - b) > 1e-7 for a, b in zip(before, after)):
                raise ValueError(f"Coordenadas OBJ distintas del origen: {key}")
    triangles = [tuple(index + 1 for index in (c, b, a))
                 for submesh in handler.get_triangles() for a, b, c in submesh]
    if [tuple(vertex[0] for vertex in face) for face in parsed["faces"]] != triangles:
        raise ValueError("Triángulos OBJ distintos del origen")
    return {"vertices": len(parsed["vertices"]), "uv": len(parsed["uv"]),
            "normals": len(parsed["normals"]), "triangles": len(triangles),
            "bounds_obj": {"min": [min(v[i] for v in parsed["vertices"]) for i in range(3)],
                           "max": [max(v[i] for v in parsed["vertices"]) for i in range(3)]},
            "positions_uv_normals_and_winding_match_source": True,
            "vertex_colors_present_in_source": bool(handler.m_Colors),
            "vertex_colors_exported": False}


def load_sources(db, candidate):
    row = db.execute("SELECT id FROM files WHERE archive=? AND logical_path=?",
                     (candidate["archive_id"], candidate["logical_path"])).fetchone()
    source, raw = checked_input(db, row["id"])
    env = UnityPy.load()
    asset = env.load_file(raw, name=source["logical_path"])
    stream = db.execute("SELECT * FROM streams WHERE owner_file=? AND object_path_id=?",
                        (source["id"], candidate["audio"]["path_id"])).fetchone()
    if stream is None or stream["range_valid"] != 1:
        raise ValueError("Stream de audio no validado")
    resource, raw_resource = checked_input(db, stream["target_file"])
    env.load_file(raw_resource, name=resource["logical_path"])
    objects = {}
    for key, kind in [("mesh", "Mesh"), ("texture", "Texture2D"), ("audio", "AudioClip")]:
        obj = asset.objects[candidate[key]["path_id"]]
        if obj.type.name != kind or obj.peek_name() != candidate[key]["name"]:
            raise ValueError(f"Candidato cambiado: {key}")
        objects[key] = obj.parse_as_object()
    materials = [obj for obj in asset.objects.values() if obj.type.name == "Material"
                 and obj.peek_name() == candidate["mesh"]["material_name"]]
    if len(materials) != 1:
        raise ValueError("El material de la muestra no es inequívoco")
    objects["material"] = materials[0].parse_as_dict()
    objects["material_path_id"] = materials[0].path_id
    return objects, [source, resource]


def export_files(objects, output):
    mesh, texture, audio = (objects[key] for key in ("mesh", "texture", "audio"))
    material = objects["material"]
    names = {key: safe_name(value.m_Name) for key, value in
             [("mesh", mesh), ("texture", texture), ("audio", audio)]}
    material_name = safe_name(material["m_Name"])
    props = material["m_SavedProperties"]
    texenv = property_map(props["m_TexEnvs"])["_MainTex"]
    if texenv["m_Texture"] != {"m_FileID": 0, "m_PathID": texture.object_reader.path_id}:
        raise ValueError("El material no apunta a la textura seleccionada")
    if texenv["m_Scale"] != {"x": 1.0, "y": 1.0} or texenv["m_Offset"] != {"x": 0.0, "y": 0.0}:
        raise ValueError("Esta muestra requiere UV sin transformación adicional del material")
    tint = property_map(props["m_Colors"])["_Color"]
    for directory in ("models", "textures", "audio"):
        (output / directory).mkdir()
    png = output / "textures" / f"{names['texture']}.png"
    image = texture.image
    image.load()
    if image.size != (texture.m_Width, texture.m_Height):
        raise ValueError("Dimensiones de textura incorrectas")
    image.save(png)
    with Image.open(png) as decoded:
        decoded.load()
        if decoded.size != image.size or decoded.tobytes() != image.tobytes():
            raise ValueError("El PNG no conserva la textura decodificada")
    obj_text = export_mesh_obj(mesh, [material_name])
    mesh_info = check_mesh_export(mesh, obj_text)
    obj = output / "models" / f"{names['mesh']}.obj"
    obj.write_text(obj_text, newline="")
    obj.with_suffix(".mtl").write_text(
        f"newmtl {material_name}\nKa 0 0 0\nKd {tint['r']:.9g} {tint['g']:.9g} {tint['b']:.9g}\n"
        f"Ks 0 0 0\nd {tint['a']:.9g}\nillum 1\nmap_Kd ../textures/{png.name}\n")
    samples = audio.samples
    if len(samples) != 1 or next(iter(samples)) != f"{names['audio']}.wav":
        raise ValueError("La prueba esperaba una única muestra WAV")
    wav_name, wav_data = next(iter(samples.items()))
    audio_info = inspect_wav(wav_data)
    if audio_info["channels"] != audio.m_Channels or audio_info["sample_rate"] != audio.m_Frequency:
        raise ValueError("Parámetros WAV distintos del AudioClip")
    if abs(audio_info["duration_seconds"] - audio.m_Length) > 1 / audio.m_Frequency:
        raise ValueError("Duración WAV distinta del AudioClip")
    (output / "audio" / wav_name).write_bytes(wav_data)
    return {
        "mesh": {"path": str(obj.relative_to(output)), **mesh_info},
        "texture": {"path": str(png.relative_to(output)), "size": image.size, "mode": image.mode,
                    "png_pixels_match_decoded_source": True, "unity_format": texture.m_TextureFormat},
        "material": {"name": material_name, "path_id": objects["material_path_id"],
                     "source_shader_pointer": material["m_Shader"], "tint_rgba": tint,
                     "original_shader_effects_not_reproduced": True},
        "audio": {"path": "audio/" + wav_name, **audio_info, "manual_listening_pending": True},
    }


def export_samples(output):
    if output.exists():
        raise FileExistsError(f"No se sobrescriben muestras existentes: {output}")
    original_hashes = {name: digest for digest, name in (line.split(maxsplit=1) for line in
                       (ROOT / "research/evidence/extraction/inputs.sha256").read_text().splitlines())}
    for name, digest in original_hashes.items():
        if sha256_file(ROOT / name) != digest:
            raise ValueError(f"SHA256 original incorrecto: {name}")
    candidate = json.loads((ROOT / "research/evidence/extraction/sample-candidates.json").read_text())
    db = sqlite3.connect((ROOT / "work/inventory/resources.sqlite").as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        objects, origins = load_sources(db, candidate)
    finally:
        db.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="samples-", dir=output.parent) as temporary:
        staging = Path(temporary) / "samples"
        staging.mkdir()
        report = export_files(objects, staging)
        report.update({"schema_version": 1, "status": "exported_technical_checks_passed",
                       "created_at_utc": datetime.now(timezone.utc).isoformat(),
                       "unitypy": version("UnityPy"), "pillow": version("Pillow"),
                       "source_files": origins, "original_sha256": original_hashes,
                       "source_path_ids": {key: candidate[key]["path_id"] for key in ("mesh", "texture", "audio")},
                       "coordinate_conversion": "UnityPy OBJ: X reflected, triangle winding reversed, UV unchanged",
                       "blender_validation_pending": True})
        report["files"] = [{"path": str(path.relative_to(staging)), "size_bytes": path.stat().st_size,
                            "sha256": sha256_file(path)} for path in sorted(staging.rglob("*")) if path.is_file()]
        for name, digest in original_hashes.items():
            if sha256_file(ROOT / name) != digest:
                raise ValueError(f"Original modificado durante la prueba: {name}")
        report["original_hashes_rechecked"] = True
        (staging / "manifest.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
        staging.rename(output)
    print(f"Muestras exportadas y comprobadas: {output}")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "exports/samples")
    args = parser.parse_args()
    export_samples(args.output.resolve())


if __name__ == "__main__":
    main()
