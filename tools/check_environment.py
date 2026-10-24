"""Comprueba el entorno y dos recursos reales sin exportar ni alterar el juego.

API de lectura: https://github.com/K0lb3/UnityPy#example
"""

from collections import Counter
from datetime import datetime, timezone
import hashlib
from importlib import metadata
import json
from pathlib import Path
import platform
import shutil
import subprocess
import sys
from zipfile import ZipFile

import UnityPy

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "research/evidence/extraction"
PROBES = {
    "Pixel Gun 3D [11.3.1].apk": "assets/bin/Data/globalgamemanagers",
    "main.1191.com.pixel.gun3d.obb": "assets/bin/Data/db4925300cb2a42829c94de804d0c2bf",
}


def check_archive(name, expected_hash):
    path = ROOT / name
    with path.open("rb") as source:
        digest = hashlib.file_digest(source, "sha256").hexdigest()
    if digest != expected_hash:
        raise RuntimeError(f"El original no coincide con su SHA256: {name}")
    member = PROBES[name]
    with ZipFile(path) as archive:
        raw = archive.read(member)  # Comprueba también el CRC de este miembro.
        entry_count = len(archive.infolist())
        unpacked_bytes = sum(info.file_size for info in archive.infolist())
    env = UnityPy.load(raw)
    objects = list(env.objects)
    versions = sorted({obj.assets_file.unity_version for obj in objects})
    if versions != ["5.3.7p1"]:
        raise RuntimeError(f"Versión inesperada o archivo sin objetos: {name}")
    textures = []
    for obj in objects:
        if obj.type.name == "Texture2D":
            texture = obj.parse_as_object()
            image = texture.image
            image.load()  # Decodificación en memoria; no genera un PNG.
            if image.size != (texture.m_Width, texture.m_Height) or min(image.size) <= 0:
                raise RuntimeError(f"Dimensiones incorrectas: {texture.m_Name}")
            textures.append({"name": texture.m_Name, "size": image.size, "mode": image.mode})
    if name.endswith(".obb") and not textures:
        raise RuntimeError("La prueba del OBB no encontró la textura esperada")
    return {
        "path": name, "size_bytes": path.stat().st_size, "sha256": digest,
        "sha256_matches_baseline": True, "zip_entries": entry_count,
        "zip_uncompressed_bytes": unpacked_bytes,
        "probe": {"member": member, "bytes": len(raw), "unity_versions": versions,
                  "object_types": dict(Counter(obj.type.name for obj in objects)),
                  "decoded_textures": textures},
    }


def main():
    if sys.prefix == sys.base_prefix:
        raise RuntimeError("Ejecuta este script con uv run --locked tools/check_environment.py")
    inputs = []
    for line in (EVIDENCE / "inputs.sha256").read_text().splitlines():
        digest, name = line.split(maxsplit=1)
        inputs.append(check_archive(name, digest))
    blender = Path("/Applications/Blender.app/Contents/MacOS/Blender")
    blender_version = None
    if blender.is_file():
        result = subprocess.run([str(blender), "--version"], capture_output=True,
                                text=True, check=True, timeout=30)
        blender_version = result.stdout.splitlines()[0]
    report = {
        "status": "ok", "scope": "phase_1_environment_only",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(), "executable": sys.executable,
        "environment_manager": "uv",
        "uv_lock_sha256": hashlib.sha256((ROOT / "uv.lock").read_bytes()).hexdigest(),
        "platform": platform.platform(), "machine": platform.machine(),
        "disk_free_bytes": shutil.disk_usage(ROOT).free,
        "dependencies": dict(sorted((dist.metadata["Name"], dist.version)
                                    for dist in metadata.distributions())),
        "blender": {"path": str(blender), "version": blender_version},
        "inputs": inputs,
        "limitations": ["Solo se leen dos miembros; no es un inventario completo.",
                        "No se verifican todos los CRC del ZIP ni referencias externas.",
                        "No se han validado exportaciones de mallas ni audio."],
    }
    output = EVIDENCE / "environment-check.json"
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print(f"OK: entorno, SHA256 y lectura APK/OBB. Informe: {output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
