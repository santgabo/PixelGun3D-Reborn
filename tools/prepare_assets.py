"""Prepara copias de datos Unity; nunca extrae ZIP directamente sobre el proyecto."""

import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
DATA_PREFIX = "assets/bin/Data/"
ARCHIVES = {
    "apk": "Pixel Gun 3D [11.3.1].apk",
    "obb": "main.1191.com.pixel.gun3d.obb",
}


def member_groups(infos):
    """Agrupa splitN en orden numérico y rechaza rutas/fragmentos ambiguos."""
    seen = set()
    groups = defaultdict(list)
    for info in infos:
        name = info.filename
        if name in seen:
            raise ValueError(f"Entrada ZIP repetida: {name}")
        seen.add(name)
        if info.is_dir() or not name.startswith(DATA_PREFIX):
            continue
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name or str(path) != name:
            raise ValueError(f"Ruta ZIP insegura: {name}")
        if stat.S_ISLNK(info.external_attr >> 16):
            raise ValueError(f"Enlace ZIP no permitido: {name}")
        match = re.fullmatch(r"(.+)\.split(\d+)", name)
        logical, index = (match[1], int(match[2])) if match else (name, None)
        if str(PurePosixPath(logical)) != logical:
            raise ValueError(f"Nombre lógico inválido: {logical}")
        groups[logical].append((index, info))
    result = {}
    for logical, parts in sorted(groups.items()):
        indices = [index for index, _ in parts]
        if None in indices:
            if len(parts) != 1:
                raise ValueError(f"Archivo completo y fragmentado a la vez: {logical}")
        else:
            if sorted(indices) != list(range(len(parts))):
                raise ValueError(f"Fragmentos ausentes o repetidos: {logical}: {indices}")
            parts.sort(key=lambda part: part[0])
        result[logical] = [info for _, info in parts]
    return result


def sha256_file(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def prepare_archive(archive_id, source, staging):
    rows = []
    with ZipFile(source) as archive:
        infos = archive.infolist()
        groups = member_groups(infos)
        for logical, parts in groups.items():
            relative = f"{archive_id}/{logical}"
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            digest = hashlib.sha256()
            size = 0
            with target.open("xb") as output:
                for info in parts:
                    with archive.open(info) as member:
                        while chunk := member.read(1024 * 1024):
                            output.write(chunk)
                            digest.update(chunk)
                            size += len(chunk)
            if size != sum(info.file_size for info in parts):
                raise ValueError(f"Tamaño recompuesto incorrecto: {logical}")
            rows.append({"archive": archive_id, "logical_path": logical,
                         "prepared_path": relative, "size_bytes": size,
                         "sha256": digest.hexdigest(),
                         "members": [info.filename for info in parts]})
        entries = [{"path": info.filename, "size_bytes": info.file_size,
                    "compressed_bytes": info.compress_size, "crc32": f"{info.CRC:08x}",
                    "prepared": info.filename.startswith(DATA_PREFIX) and not info.is_dir()}
                   for info in infos]
    return rows, entries


def prepare(output):
    if output.exists():
        raise FileExistsError(f"No se sobrescribe una preparación existente: {output}")
    baselines = ROOT / "research/evidence/extraction/inputs.sha256"
    expected = {name: digest for digest, name in
                (line.split(maxsplit=1) for line in baselines.read_text().splitlines())}
    if set(expected) != set(ARCHIVES.values()):
        raise ValueError("El registro SHA256 no contiene exactamente los dos paquetes")
    for name, digest in expected.items():
        if sha256_file(ROOT / name) != digest:
            raise ValueError(f"SHA256 original incorrecto: {name}")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="prepare-", dir=output.parent) as temporary:
        staging = Path(temporary) / "prepared"
        staging.mkdir()
        files, archives = [], []
        for archive_id, name in ARCHIVES.items():
            rows, entries = prepare_archive(archive_id, ROOT / name, staging)
            files.extend(rows)
            archives.append({"id": archive_id, "path": name, "sha256": expected[name],
                             "size_bytes": (ROOT / name).stat().st_size, "entries": entries})
            print(f"{archive_id}: {len(entries)} entradas, {len(rows)} archivos preparados", flush=True)
        for name, digest in expected.items():
            if sha256_file(ROOT / name) != digest:
                raise ValueError(f"El original cambió durante la preparación: {name}")
        manifest = {
            "schema_version": 1, "status": "ok",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "scope": "Unity data only; other archive entries listed but not copied",
            "original_hashes_rechecked": True, "prepared_members_crc_checked": True,
            "archives": archives, "files": files,
        }
        (staging / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        staging.rename(output)
    print(f"Preparación completa: {output}")
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "work/prepared")
    args = parser.parse_args()
    prepare(args.output.resolve())


if __name__ == "__main__":
    main()
