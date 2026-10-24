"""Inventario SQLite de datos Unity preparados, sin exportación ni decodificación.

API: https://github.com/K0lb3/UnityPy#important-classes
Ejecutar desde la raíz: uv run --locked -m tools.inventory_assets
"""

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import sqlite3
import sys
import tempfile

import UnityPy
from UnityPy.enums import FileType
from UnityPy.files import SerializedFile
from UnityPy.helpers.ImportHelper import check_file_type

from tools.inventory_refs import FileIndex, pointers, stream_descriptors
from tools.prepare_assets import sha256_file

ROOT = Path(__file__).resolve().parents[1]
PARSE_TYPES = {"Texture2D", "Mesh", "AudioClip", "Material", "MeshFilter", "MeshRenderer",
               "SkinnedMeshRenderer", "Sprite", "ResourceManager", "AssetBundle"}
LINK_FIELDS = {"m_Mesh", "m_Materials", "m_GameObject", "m_Shader", "m_SavedProperties", "m_RD"}


def create_database(path, files):
    db = sqlite3.connect(path)
    db.executescript("""
        PRAGMA foreign_keys=ON;
        CREATE TABLE files (
            id INTEGER PRIMARY KEY, archive TEXT, logical_path TEXT, prepared_path TEXT UNIQUE,
            size_bytes INTEGER, sha256 TEXT, kind TEXT, unity_version TEXT,
            object_count INTEGER DEFAULT 0, status TEXT DEFAULT 'pending');
        CREATE TABLE objects (
            file_id INTEGER REFERENCES files(id), path_id INTEGER, class_id INTEGER, type TEXT,
            name TEXT, name_status TEXT, byte_start INTEGER, byte_size INTEGER, details_json TEXT,
            PRIMARY KEY(file_id, path_id));
        CREATE TABLE externals (
            owner_file INTEGER REFERENCES files(id), external_id INTEGER, path TEXT, guid TEXT,
            type INTEGER, target_file INTEGER REFERENCES files(id), resolution TEXT, candidates_json TEXT,
            PRIMARY KEY(owner_file, external_id));
        CREATE TABLE links (
            owner_file INTEGER REFERENCES files(id), object_path_id INTEGER, field TEXT, kind TEXT,
            logical_name TEXT, target_file_id INTEGER, target_path_id INTEGER,
            target_file INTEGER REFERENCES files(id), resolution TEXT);
        CREATE TABLE streams (
            owner_file INTEGER REFERENCES files(id), object_path_id INTEGER, field TEXT, path TEXT,
            offset INTEGER, size INTEGER, target_file INTEGER REFERENCES files(id), resolution TEXT,
            range_valid INTEGER, candidates_json TEXT);
        CREATE TABLE errors (
            owner_file INTEGER REFERENCES files(id), object_path_id INTEGER, stage TEXT, message TEXT);
    """)
    db.executemany("INSERT INTO files(id,archive,logical_path,prepared_path,size_bytes,sha256) "
                   "VALUES(:id,:archive,:logical_path,:prepared_path,:size_bytes,:sha256)", files)
    db.commit()
    return db


def add_error(db, file_id, path_id, stage, error):
    db.execute("INSERT INTO errors VALUES(?,?,?,?)", (file_id, path_id, stage, str(error)))


def details(data):
    result = {key: data[key] for key in (
        "m_Width", "m_Height", "m_TextureFormat", "m_CompleteImageSize", "m_Length",
        "m_Channels", "m_Frequency", "m_CompressionFormat", "m_SubsoundIndex") if key in data}
    if "m_VertexData" in data:
        result["vertex_count"] = data["m_VertexData"].get("m_VertexCount")
        result["submesh_count"] = len(data.get("m_SubMeshes", []))
    return result


def record_data(db, index, file_id, obj, data):
    selected = {key: data[key] for key in LINK_FIELDS if key in data}
    links = [(file_id, obj.path_id, field, "reference", None, fid, pid)
             for field, fid, pid in pointers(selected)]
    if obj.type.name in {"ResourceManager", "AssetBundle"}:
        for position, (name, value) in enumerate(data.get("m_Container", [])):
            ptr = value["asset"] if obj.type.name == "AssetBundle" else value
            links.append((file_id, obj.path_id, f"m_Container[{position}]", "resource_name",
                          name, ptr["m_FileID"], ptr["m_PathID"]))
    db.executemany("INSERT INTO links(owner_file,object_path_id,field,kind,logical_name,"
                   "target_file_id,target_path_id) VALUES(?,?,?,?,?,?,?)", links)
    for field, path, offset, size in stream_descriptors(data):
        target, method, candidates = index.resolve(file_id, path)
        valid = None if target is None else int(0 <= offset and 0 <= size and
                                               offset + size <= index.by_id[target]["size_bytes"])
        db.execute("INSERT INTO streams VALUES(?,?,?,?,?,?,?,?,?,?)",
                   (file_id, obj.path_id, field, path, offset, size, target, method,
                    valid, json.dumps(candidates)))


def inventory_object(db, index, file_id, obj):
    errors = 0
    data = None
    if obj.type.name in PARSE_TYPES:
        try:
            data = obj.parse_as_dict()
        except Exception as error:
            errors += 1
            add_error(db, file_id, obj.path_id, "object_fields", error)
    try:
        name = data["m_Name"] if data is not None and "m_Name" in data else obj.peek_name()
        name_status = "not_applicable" if name is None else "empty" if name == "" else "ok"
    except Exception as error:
        errors += 1
        name, name_status = None, "error"
        add_error(db, file_id, obj.path_id, "object_name", error)
    db.execute("INSERT INTO objects VALUES(?,?,?,?,?,?,?,?,?)",
               (file_id, obj.path_id, obj.class_id, obj.type.name, name, name_status,
                obj.byte_start, obj.byte_size, json.dumps(details(data or {}))))
    if data is not None:
        record_data(db, index, file_id, obj, data)
    return errors


def inventory_file(db, index, root, row):
    file_id = row["id"]
    try:
        raw = (root / row["prepared_path"]).read_bytes()
        if hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError("El archivo preparado no coincide con su SHA256")
        kind, _ = check_file_type(raw)
        db.execute("UPDATE files SET kind=? WHERE id=?", (kind.name, file_id))
        if kind == FileType.ResourceFile:
            db.execute("UPDATE files SET status='ok' WHERE id=?", (file_id,))
            return
        if kind != FileType.AssetsFile:
            raise ValueError(f"Contenedor no cubierto por este inventario: {kind.name}")
        env = UnityPy.load(raw)
        assets = [value for value in env.files.values() if isinstance(value, SerializedFile)]
        if len(assets) != 1:
            raise ValueError(f"Se esperaba un archivo serializado; encontrados: {len(assets)}")
        asset = assets[0]
    except Exception as error:
        add_error(db, file_id, None, "file_load", error)
        db.execute("UPDATE files SET status='error' WHERE id=?", (file_id,))
        return
    for external_id, external in enumerate(asset.externals, 1):
        target, method, candidates = index.resolve(file_id, external.path)
        db.execute("INSERT INTO externals VALUES(?,?,?,?,?,?,?,?)",
                   (file_id, external_id, external.path, external.guid.hex() if external.guid else None,
                    external.type, target, method, json.dumps(candidates)))
    errors = 0
    for obj in asset.objects.values():
        if not (0 <= obj.byte_start <= obj.byte_start + obj.byte_size <= len(raw)):
            errors += 1
            add_error(db, file_id, obj.path_id, "object_range", "Objeto fuera del archivo")
        errors += inventory_object(db, index, file_id, obj)
    db.execute("UPDATE files SET unity_version=?,object_count=?,status=? WHERE id=?",
               (asset.unity_version, len(asset.objects), "partial" if errors else "ok", file_id))


def resolve_links(db):
    db.executescript("""
        UPDATE links SET target_file = CASE
            WHEN target_path_id=0 THEN NULL
            WHEN target_file_id=0 THEN owner_file
            ELSE (SELECT target_file FROM externals e
                  WHERE e.owner_file=links.owner_file AND e.external_id=links.target_file_id) END;
        UPDATE links SET resolution = CASE
            WHEN target_path_id=0 THEN 'null'
            WHEN target_file_id<0 OR (target_file_id>0 AND NOT EXISTS
                (SELECT 1 FROM externals e WHERE e.owner_file=links.owner_file
                 AND e.external_id=links.target_file_id)) THEN 'invalid_file_id'
            WHEN target_file IS NULL THEN 'unresolved_file'
            WHEN NOT EXISTS (SELECT 1 FROM objects o
                 WHERE o.file_id=links.target_file AND o.path_id=links.target_path_id)
                 THEN 'missing_object'
            ELSE 'resolved' END;
        CREATE INDEX objects_type_name ON objects(type,name);
        CREATE INDEX links_target ON links(target_file,target_path_id);
        CREATE INDEX links_logical_name ON links(logical_name);
    """)


def counts(db, table, column):
    return dict(db.execute(f"SELECT {column},count(*) FROM {table} GROUP BY {column}").fetchall())


def make_summary(db, manifest):
    total = lambda table: db.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
    missing_files = db.execute("SELECT count(*) FROM externals WHERE target_file IS NULL").fetchone()[0]
    broken_links = db.execute("SELECT count(*) FROM links WHERE resolution NOT IN ('resolved','null')").fetchone()[0]
    broken_streams = db.execute("SELECT count(*) FROM streams WHERE target_file IS NULL OR range_valid<>1").fetchone()[0]
    prepared_members = sum(len(row["members"]) for row in manifest["files"])
    entries = sum(len(archive["entries"]) for archive in manifest["archives"])
    return {
        "schema_version": 1,
        "status": "warnings" if total("errors") or missing_files or broken_links or broken_streams else "ok",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0], "unitypy": version("UnityPy"),
        "coverage": {"archive_entries": entries, "prepared_members": prepared_members,
                     "other_entries_listed_not_copied": entries - prepared_members,
                     "prepared_files": len(manifest["files"]),
                     "prepared_bytes": sum(row["size_bytes"] for row in manifest["files"]),
                     "reassembled_groups": sum(len(row["members"]) > 1 for row in manifest["files"])},
        "files": {"total": total("files"), "by_kind": counts(db, "files", "kind"),
                  "by_status": counts(db, "files", "status"),
                  "unity_versions": counts(db, "files", "unity_version")},
        "objects": {"total": total("objects"), "by_type": counts(db, "objects", "type"),
                    "names": counts(db, "objects", "name_status")},
        "externals": {"total": total("externals"), "unresolved": missing_files,
                      "methods": counts(db, "externals", "resolution")},
        "links": {"total": total("links"), "broken": broken_links,
                  "by_kind": counts(db, "links", "kind"), "resolutions": counts(db, "links", "resolution")},
        "streams": {"total": total("streams"), "broken": broken_streams,
                    "methods": counts(db, "streams", "resolution"),
                    "range_valid": counts(db, "streams", "range_valid")},
        "errors": {"total": total("errors"), "by_stage": counts(db, "errors", "stage")},
        "limits": ["Solo datos bajo assets/bin/Data; otras entradas están listadas en el manifiesto.",
                   "Campos completos de diez tipos relevantes; para otros tipos se intenta solo m_Name.",
                   "No se interpretan campos personalizados de scripts, esqueletos ni animaciones.",
                   "No se decodifican ni exportan imágenes, mallas ni sonidos.",
                   "Resolver una referencia y validar su rango no demuestra fidelidad visual o sonora."],
    }


def write_logs(db, output):
    db.row_factory = sqlite3.Row
    context = ",f.archive AS owner_archive,f.logical_path AS owner_path"
    with (output / "errors.jsonl").open("w") as log:
        for row in db.execute("SELECT e.*" + context + " FROM errors e JOIN files f ON f.id=e.owner_file"):
            log.write(json.dumps(dict(row), ensure_ascii=False) + "\n")
    with (output / "unresolved-references.jsonl").open("w") as log:
        for table, condition in [
            ("externals", "e.target_file IS NULL"),
            ("links", "e.resolution NOT IN ('resolved','null')"),
            ("streams", "e.target_file IS NULL OR e.range_valid<>1"),
        ]:
            query = f"SELECT e.*{context} FROM {table} e JOIN files f ON f.id=e.owner_file WHERE {condition}"
            for row in db.execute(query):
                log.write(json.dumps({"record_type": table, **dict(row)}, ensure_ascii=False) + "\n")


def inventory(prepared, output):
    if output.exists():
        raise FileExistsError(f"No se sobrescribe un inventario existente: {output}")
    manifest = json.loads((prepared / "manifest.json").read_text())
    if manifest["schema_version"] != 1 or manifest["status"] != "ok":
        raise ValueError("Manifiesto de preparación no validado")
    files = [dict(row, id=index) for index, row in enumerate(manifest["files"], 1)]
    index = FileIndex(files)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="inventory-", dir=output.parent) as temporary:
        staging = Path(temporary) / "inventory"
        staging.mkdir()
        db = create_database(staging / "resources.sqlite", files)
        try:
            for position, row in enumerate(files, 1):
                inventory_file(db, index, prepared, row)
                if position % 500 == 0 or position == len(files):
                    db.commit()
                    print(f"Inventariados {position}/{len(files)} archivos", flush=True)
            resolve_links(db)
            db.commit()
            if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok" or db.execute("PRAGMA foreign_key_check").fetchall():
                raise RuntimeError("Falló la integridad de la base de datos")
            summary = make_summary(db, manifest)
            for archive in manifest["archives"]:
                if sha256_file(ROOT / archive["path"]) != archive["sha256"]:
                    raise RuntimeError(f"Original modificado: {archive['path']}")
            summary["original_hashes_rechecked"] = True
            (staging / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
            write_logs(db, staging)
        finally:
            db.close()
        staging.rename(output)
    print(f"Inventario completo: {output}; estado: {summary['status']}")
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepared", type=Path, default=ROOT / "work/prepared")
    parser.add_argument("--output", type=Path, default=ROOT / "work/inventory")
    args = parser.parse_args()
    summary = inventory(args.prepared.resolve(), args.output.resolve())
    return 0 if summary["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
