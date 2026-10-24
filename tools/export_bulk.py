"""Extrae texturas, sprites, mallas estáticas y sonidos por lotes.

No exporta esqueletos, pesos ni animaciones. Una malla con pose de bind sale en
su pose de reposo. El OBJ refleja X e invierte el winding, igual que UnityPy,
y no modifica las UV. Se puede reanudar: un recurso con estado ok y el mismo
SHA256 no se vuelve a escribir.

    uv run --locked -m tools.export_bulk --profile trial --output exports/bulk
    uv run --locked -m tools.export_bulk --output exports/bulk
"""

import argparse
import array
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import sqlite3
import sys
import wave

from PIL import Image
import UnityPy
from UnityPy.helpers.MeshHelper import MeshHandler

from tools.export_samples import property_map
from tools.prepare_assets import sha256_file

ROOT = Path(__file__).resolve().parents[1]
KIND_TYPES = {"texture": "Texture2D", "sprite": "Sprite", "audio": "AudioClip", "mesh": "Mesh"}
TYPE_KINDS = {value: key for key, value in KIND_TYPES.items()}
KIND_ORDER = {"texture": 0, "sprite": 1, "audio": 2, "mesh": 3}
EXPORTER_REVISION = 2
FOLDERS = {"texture": "textures", "sprite": "sprites", "audio": "audio", "mesh": "models"}
AUDIO_EXTENSIONS = {".wav", ".ogg", ".m4a"}
PINNED = (
    ("mesh", "obb", "assets/bin/Data/sharedassets104.assets", "School_menu_bench2"),
    ("texture", "obb", "assets/bin/Data/sharedassets104.assets", "school_menu_atlas"),
    ("audio", "obb", "assets/bin/Data/sharedassets104.assets", "Bells_lobby"),
    ("mesh", "obb", "assets/bin/Data/47f34ace77a313c4e9cbfa48107beff5", "PixlGun_Mesh"),
    ("texture", "obb", "assets/bin/Data/bb9c08d0a2b036641874e7977d1b5c66", "PixelGun_2.0_map"),
    ("audio", "obb", "assets/bin/Data/bbf7b2eeb07f36447b71815024142b60", "PixlGun_Shoot"),
)
RESERVED = (
    "exports/samples", "exports/samples-weapon", "work/prepared", "work/inventory", "work",
)


def safe_stem(name):
    """Un solo componente de archivo. path_id distingue los nombres repetidos."""
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", "" if name is None else str(name))
    cleaned = re.sub(r"_+", "_", cleaned).strip("._")
    return (cleaned or "unnamed")[:80]


def logical_parts(logical_path):
    if not logical_path or "\\" in logical_path or logical_path.startswith("/"):
        raise ValueError(f"Ruta de origen no usable: {logical_path!r}")
    path = PurePosixPath(logical_path)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError(f"Ruta de origen no usable: {logical_path!r}")
    return path.parts


def item_relative_path(kind, archive, logical_path, path_id, name, suffix):
    if kind not in FOLDERS or archive not in {"apk", "obb"} or not isinstance(path_id, int) or isinstance(path_id, bool):
        raise ValueError(f"Identidad de salida no válida: {kind} {archive} {path_id}")
    if suffix not in {".png", ".obj", ".mtl", ".wav", ".ogg", ".m4a", ".bin"}:
        raise ValueError(f"Extensión no permitida: {suffix}")
    filename = f"{path_id}_{safe_stem(name)}{suffix}"
    return PurePosixPath(FOLDERS[kind], archive, *logical_parts(logical_path), filename)


def inside(root, path):
    resolved = path.resolve()
    base = root.resolve()
    return resolved == base or base in resolved.parents


def relative_reference(source, target):
    return Path(os.path.relpath(target, source.parent)).as_posix()


def error_text(error):
    text = f"{type(error).__name__}: {error}"
    return text if len(text) <= 500 else text[:497] + "..."


def finite(value, replaced):
    number = float(value)
    if not math.isfinite(number):
        replaced[0] += 1
        return 0.0
    return number


def build_obj(stem, mtl_filename, vertices, uvs, normals, submeshes, material_names):
    """Convierte una malla Unity a OBJ. Devuelve el texto y la geometría saneada."""
    replaced = [0]
    positions = [(finite(-float(vertex[0]), replaced), finite(vertex[1], replaced), finite(vertex[2], replaced))
                 for vertex in vertices]
    use_uv = len(uvs) == len(vertices) and len(vertices) > 0
    use_normals = len(normals) == len(vertices) and len(vertices) > 0
    uv_out = [tuple(finite(value, replaced) for value in uv[:2]) for uv in uvs] if use_uv else []
    normal_out = [(finite(-float(normal[0]), replaced), finite(normal[1], replaced), finite(normal[2], replaced))
                  for normal in normals] if use_normals else []
    lines = [f"g {stem}", f"mtllib {mtl_filename}"] if mtl_filename else [f"g {stem}"]
    lines.extend(f"v {x:.9g} {y:.9g} {z:.9g}" for x, y, z in positions)
    lines.extend(f"vt {u:.9g} {v:.9g}" for u, v in uv_out)
    lines.extend(f"vn {x:.9g} {y:.9g} {z:.9g}" for x, y, z in normal_out)
    for index, triangles in enumerate(submeshes):
        lines.append(f"g {stem}_{index}")
        material = material_names[index] if index < len(material_names) else None
        if material:
            lines.append(f"usemtl {material}")
        for first, second, third in triangles:
            # UnityPy escribe el triángulo como (c, b, a): winding invertido.
            for vertex in (third, second, first):
                if not 0 <= vertex < len(positions):
                    raise ValueError("Índice de malla fuera de rango")
            tokens = []
            for vertex in (third, second, first):
                number = vertex + 1
                if use_uv and use_normals:
                    tokens.append(f"{number}/{number}/{number}")
                elif use_uv:
                    tokens.append(f"{number}/{number}")
                elif use_normals:
                    tokens.append(f"{number}//{number}")
                else:
                    tokens.append(str(number))
            lines.append("f " + " ".join(tokens))
    info = {"vertices": len(positions), "uv": len(uv_out), "normals": len(normal_out),
            "triangles": sum(len(submesh) for submesh in submeshes), "non_finite_replaced": replaced[0],
            "uv_exported": use_uv, "normals_exported": use_normals}
    return "\n".join(lines) + "\n", positions, uv_out, normal_out, info


def parse_obj(text):
    vertices, uv, normals, faces = [], [], [], []
    for line in text.splitlines():
        parts = line.split()
        if not parts or parts[0].startswith("#") or parts[0] in {"g", "mtllib", "usemtl", "o", "s"}:
            continue
        if parts[0] == "v":
            vertices.append(tuple(map(float, parts[1:4])))
        elif parts[0] == "vt":
            uv.append(tuple(map(float, parts[1:3])))
        elif parts[0] == "vn":
            normals.append(tuple(map(float, parts[1:4])))
        elif parts[0] == "f":
            if len(parts) != 4:
                raise ValueError("Cara OBJ que no es un triángulo")
            faces.append(parts[1:])
    return vertices, uv, normals, faces


def assert_close(actual, expected, label):
    """Tolera el redondeo de nueve cifras. Una UV de lightmap puede pasar de 10 000."""
    if len(actual) != len(expected):
        raise ValueError(f"Cantidad OBJ distinta: {label}")
    for left, right in zip(actual, expected):
        if any(abs(a - b) > 1e-5 * max(1.0, abs(b)) for a, b in zip(left, right)):
            raise ValueError(f"Coordenadas OBJ distintas: {label}")


def check_obj_text(text, positions, uvs, normals, submeshes):
    parsed_vertices, parsed_uv, parsed_normals, faces = parse_obj(text)
    assert_close(parsed_vertices, positions, "posiciones")
    assert_close(parsed_uv, uvs, "uv")
    assert_close(parsed_normals, normals, "normales")
    expected = [f"{vertex + 1}" for submesh in submeshes for a, b, c in submesh for vertex in (c, b, a)]
    actual = [token.split("/")[0] for face in faces for token in face]
    if actual != expected:
        raise ValueError("Triángulos OBJ distintos del origen")
    if not parsed_vertices or not faces:
        raise ValueError("OBJ sin geometría")


def near(pair, origin, tolerance=1e-5):
    return abs(pair[0] - origin[0]) <= tolerance and abs(pair[1] - origin[1]) <= tolerance


def rgba(color):
    if color is None:
        return (1.0, 1.0, 1.0, 1.0)
    source = color if isinstance(color, dict) else {"r": color.r, "g": color.g, "b": color.b, "a": color.a}
    return tuple(float(source[channel]) for channel in ("r", "g", "b", "a"))


def vec2(value):
    source = value if isinstance(value, dict) else {"x": value.x, "y": value.y}
    return (float(source["x"]), float(source["y"]))


def component(value, key):
    return value[key] if isinstance(value, dict) else getattr(value, key)


def slot_signature(renderer):
    return tuple((slot["index"], slot.get("resolution"), slot.get("target_file"), slot.get("target_path_id"))
                 for slot in renderer["slots"])


def material_groups(renderers):
    grouped = {}
    for renderer in renderers:
        grouped.setdefault(slot_signature(renderer), []).append(renderer)
    return list(grouped.values())


def ordered_groups(renderers, mesh_file_id, submesh_count):
    """Primero la asignación que encaja con los submeshes y más renderers comparten."""
    def rank(group):
        return (len(group[0]["slots"]) != submesh_count, -len(group),
                all(renderer["file_id"] != mesh_file_id for renderer in group),
                min((renderer["file_id"], renderer["path_id"]) for renderer in group))

    return sorted(material_groups(renderers), key=rank)


def choose_renderer(renderers, mesh_file_id):
    groups = material_groups(renderers)
    if not groups:
        return None, "missing"
    chosen_group = ordered_groups(renderers, mesh_file_id, len(renderers[0]["slots"]))[0]
    chosen = min(chosen_group, key=lambda renderer: (
        renderer["file_id"] != mesh_file_id, renderer["file_id"], renderer["path_id"]))
    return chosen, "unique" if len(groups) == 1 else "ambiguous"


class Journal:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS items (
                kind TEXT NOT NULL, file_id INTEGER NOT NULL, path_id INTEGER NOT NULL,
                archive TEXT NOT NULL, logical_path TEXT NOT NULL, name TEXT,
                status TEXT NOT NULL, output_json TEXT, detail_json TEXT, error TEXT,
                updated_at TEXT NOT NULL, PRIMARY KEY (kind, file_id, path_id));
        """)
        self.db.commit()

    def get(self, kind, file_id, path_id):
        return self.db.execute("SELECT * FROM items WHERE kind=? AND file_id=? AND path_id=?",
                               (kind, file_id, path_id)).fetchone()

    def put(self, item):
        self.db.execute("""
            INSERT INTO items(kind,file_id,path_id,archive,logical_path,name,status,output_json,
                              detail_json,error,updated_at)
            VALUES(:kind,:file_id,:path_id,:archive,:logical_path,:name,:status,:output_json,
                   :detail_json,:error,:updated_at)
            ON CONFLICT(kind,file_id,path_id) DO UPDATE SET
                archive=excluded.archive, logical_path=excluded.logical_path, name=excluded.name,
                status=excluded.status, output_json=excluded.output_json,
                detail_json=excluded.detail_json, error=excluded.error, updated_at=excluded.updated_at
        """, item)
        self.db.commit()

    def rows(self):
        return list(self.db.execute("SELECT * FROM items ORDER BY kind, file_id, path_id"))

    def close(self):
        self.db.close()


def outputs_match(output, records):
    if not records:
        return False
    for record in records:
        path = output / record["path"]
        if not path.is_file() or path.is_symlink() or not inside(output, path):
            return False
        if path.stat().st_size != record["size_bytes"] or sha256_file(path) != record["sha256"]:
            return False
    return True


def decide(record, output):
    """skip solo cuando el resultado ya se comprobó con esta revisión. failed se repite."""
    if record is None or record["status"] == "failed":
        return "export"
    detail = json.loads(record["detail_json"] or "{}")
    if detail.get("exporter_revision") != EXPORTER_REVISION:
        return "export"
    if record["status"] == "skipped":
        return "skip"
    if record["status"] == "ok" and outputs_match(output, json.loads(record["output_json"] or "[]")):
        return "skip"
    return "export"


def prepare_output(output):
    output = output.resolve()
    root = ROOT.resolve()
    if output == root or root not in output.parents:
        raise ValueError(f"El destino tiene que estar dentro del proyecto: {output}")
    for relative in RESERVED:
        reserved = (root / relative).resolve()
        if output == reserved or reserved in output.parents:
            raise ValueError(f"Destino reservado: {output}")
    output.mkdir(parents=True, exist_ok=True)
    journal = output / "journal.sqlite"
    if journal.exists():
        return output
    if any(output.iterdir()):
        raise FileExistsError(f"El destino no tiene diario y no se va a mezclar: {output}")
    return output


def cleanup_partials(output):
    for path in output.rglob("*.partial"):
        if path.is_file() and not path.is_symlink() and inside(output, path):
            path.unlink()


def publish(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".partial")
    if isinstance(data, str):
        temporary.write_text(data, newline="\n")
    else:
        temporary.write_bytes(data)
    os.replace(temporary, path)


def file_record(output, path):
    relative = path.resolve().relative_to(output.resolve()).as_posix()
    return {"path": relative, "size_bytes": path.stat().st_size, "sha256": sha256_file(path)}


def original_hashes():
    lines = (ROOT / "research/evidence/extraction/inputs.sha256").read_text().splitlines()
    return {name: digest for digest, name in (line.split(maxsplit=1) for line in lines if line.strip())}


def assert_originals(expected):
    for name, digest in expected.items():
        if sha256_file(ROOT / name) != digest:
            raise ValueError(f"SHA256 original incorrecto: {name}")


def load_catalog(db):
    rows = []
    for row in db.execute("""
        SELECT o.file_id, o.path_id, o.type, o.name, o.details_json, f.archive, f.logical_path, f.sha256
        FROM objects o JOIN files f ON f.id=o.file_id
        WHERE o.type IN ('Texture2D','Sprite','AudioClip','Mesh') AND f.status IN ('ok','partial')
        ORDER BY o.file_id, o.path_id
    """):
        item = dict(row)
        item["kind"] = TYPE_KINDS[item["type"]]
        rows.append(item)
    return rows


def trial_subset(rows):
    index = {(row["kind"], row["archive"], row["logical_path"], row["name"]): row for row in rows}
    missing = [key for key in PINNED if key not in index]
    if missing:
        raise ValueError(f"El lote de prueba no encuentra muestras conocidas: {missing}")
    chosen, seen = [], set()

    def add(row):
        identity = (row["kind"], row["file_id"], row["path_id"])
        if identity not in seen:
            seen.add(identity)
            chosen.append(row)

    for key in PINNED:
        add(index[key])

    def number(row, key):
        value = json.loads(row["details_json"] or "{}").get(key)
        return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None

    for predicate in (
        lambda row: row["kind"] == "texture" and number(row, "m_Width") == 0,
        lambda row: row["kind"] == "mesh" and number(row, "vertex_count") == 0,
        lambda row: row["kind"] == "mesh" and (number(row, "submesh_count") or 0) >= 2
        and (number(row, "vertex_count") or 0) > 0,
    ):
        for row in rows:
            if predicate(row):
                add(row)
                break
    formats, extra = set(), 0
    for row in rows:
        if row["kind"] != "texture":
            continue
        details = json.loads(row["details_json"] or "{}")
        if (details.get("m_Width") or 0) <= 0 or details.get("m_TextureFormat") in formats:
            continue
        formats.add(details.get("m_TextureFormat"))
        add(row)
        extra += 1
        if extra >= 4:
            break
    groups = defaultdict(list)
    for row in rows:
        if row["kind"] == "texture":
            groups[row["name"]].append(row)
    for name, group in sorted(groups.items(), key=lambda item: item[0] or ""):
        if len(group) < 2 or not name:
            continue
        areas = []
        for row in group[:2]:
            details = json.loads(row["details_json"] or "{}")
            areas.append((details.get("m_Width") or 0) * (details.get("m_Height") or 0))
        if 0 < max(areas) <= 256 * 256:
            add(group[0])
            add(group[1])
            break
    sprites = audios = 0
    for row in rows:
        if row["kind"] == "sprite" and sprites < 2:
            add(row)
            sprites += 1
        elif row["kind"] == "audio" and row["name"] not in {"Bells_lobby", "PixlGun_Shoot"} and audios < 2:
            add(row)
            audios += 1
    return chosen


def select_work(rows, journal, output, profile, limit, kinds):
    selected = [row for row in rows if row["kind"] in kinds]
    if profile == "trial":
        selected = [row for row in trial_subset(rows) if row["kind"] in kinds]
    selected.sort(key=lambda row: (KIND_ORDER[row["kind"]], row["file_id"], row["path_id"]))
    work, counts = [], Counter()
    for row in selected:
        if decide(journal.get(row["kind"], row["file_id"], row["path_id"]), output) == "skip":
            continue
        if limit and counts[row["kind"]] >= limit:
            continue
        counts[row["kind"]] += 1
        work.append(row)
    return work


class Catalog:
    def __init__(self, db, cache_size=12):
        self.db = db
        self.cache_size = cache_size
        self.envs = {}
        self.order = []
        self.rows = {}

    def file_row(self, file_id):
        if file_id not in self.rows:
            row = self.db.execute("SELECT * FROM files WHERE id=?", (file_id,)).fetchone()
            if row is None or row["status"] not in {"ok", "partial"}:
                raise ValueError(f"Archivo de catálogo no usable: {file_id}")
            self.rows[file_id] = dict(row)
        return self.rows[file_id]

    def read_verified(self, file_id):
        row = self.file_row(file_id)
        path = ROOT / "work/prepared" / row["prepared_path"]
        raw = path.read_bytes()
        if hashlib.sha256(raw).hexdigest() != row["sha256"]:
            raise ValueError(f"Copia preparada modificada: {row['prepared_path']}")
        return row, raw

    def asset(self, file_id):
        if file_id in self.envs:
            self.order.remove(file_id)
            self.order.append(file_id)
            return self.envs[file_id]
        row, raw = self.read_verified(file_id)
        if row["kind"] != "AssetsFile":
            raise ValueError(f"No es un archivo serializado: {row['logical_path']}")
        env = UnityPy.load()
        loaded = env.load_file(raw, name=row["logical_path"])
        if not hasattr(loaded, "objects"):
            raise ValueError(f"Contenedor sin objetos: {row['logical_path']}")
        self.envs[file_id] = {"row": row, "env": env, "asset": loaded}
        self.order.append(file_id)
        while len(self.order) > self.cache_size:
            self.envs.pop(self.order.pop(0), None)
        return self.envs[file_id]

    def object(self, file_id, path_id):
        try:
            return self.asset(file_id)["asset"].objects[path_id]
        except KeyError:
            raise ValueError(f"path_id ausente: {file_id} {path_id}") from None


def load_renderers(db):
    types = {(file_id, path_id): kind for file_id, path_id, kind in db.execute(
        "SELECT file_id, path_id, type FROM objects WHERE type IN ('MeshFilter','MeshRenderer','SkinnedMeshRenderer')")}
    mesh_of, game_object, renderers_of_object, materials = {}, {}, defaultdict(list), defaultdict(list)
    for row in db.execute("""
        SELECT owner_file, object_path_id, field, target_file, target_path_id, resolution
        FROM links WHERE field='m_Mesh' OR field='m_GameObject' OR field LIKE 'm_Materials[%]'
    """):
        owner = (row["owner_file"], row["object_path_id"])
        kind = types.get(owner)
        if row["field"] == "m_Mesh" and row["resolution"] == "resolved" and kind in {"MeshFilter", "SkinnedMeshRenderer"}:
            mesh_of[owner] = (row["target_file"], row["target_path_id"], kind)
        elif row["field"] == "m_GameObject" and row["resolution"] == "resolved" and kind is not None:
            target = (row["target_file"], row["target_path_id"])
            game_object[owner] = target
            if kind == "MeshRenderer":
                renderers_of_object[target].append(owner)
        elif row["field"].startswith("m_Materials[") and kind in {"MeshRenderer", "SkinnedMeshRenderer"}:
            match = re.fullmatch(r"m_Materials\[(\d+)\]", row["field"])
            if match:
                materials[owner].append({"index": int(match.group(1)), "target_file": row["target_file"],
                                         "target_path_id": row["target_path_id"], "resolution": row["resolution"]})
    found = defaultdict(dict)
    for owner, (mesh_file, mesh_path, kind) in mesh_of.items():
        owners = [owner] if kind == "SkinnedMeshRenderer" else renderers_of_object.get(game_object.get(owner), [])
        for renderer_id in owners:
            slots = sorted(materials.get(renderer_id, []), key=lambda slot: slot["index"])
            found[(mesh_file, mesh_path)][renderer_id] = {
                "file_id": renderer_id[0], "path_id": renderer_id[1],
                "type": "SkinnedMeshRenderer" if kind == "SkinnedMeshRenderer" else "MeshRenderer",
                "slots": slots}
    return {key: list(value.values()) for key, value in found.items()}


def resolve_pointer(db, owner_file_id, pointer):
    if not pointer:
        return None
    file_id, path_id = component(pointer, "m_FileID"), component(pointer, "m_PathID")
    if not path_id:
        return None
    if file_id == 0:
        return owner_file_id, path_id
    row = db.execute("SELECT target_file FROM externals WHERE owner_file=? AND external_id=?",
                     (owner_file_id, file_id)).fetchone()
    if row is None or row["target_file"] is None:
        return None
    return row["target_file"], path_id


def describe_wav(data):
    with wave.open(io.BytesIO(data), "rb") as audio:
        channels, width, rate, frames = (audio.getnchannels(), audio.getsampwidth(),
                                         audio.getframerate(), audio.getnframes())
        pcm = audio.readframes(frames)
        compressed = audio.getcomptype() != "NONE"
    result = {"container": "wav", "channels": channels, "sample_width_bytes": width,
              "sample_rate": rate, "frames": frames,
              "duration_seconds": frames / rate if rate else None, "compressed": compressed}
    if width == 2 and not compressed and frames and len(pcm) == frames * channels * width:
        values = array.array("h", pcm)
        if sys.byteorder != "little":
            values.byteswap()
        peak = max((abs(value) for value in values), default=0)
        result["peak_normalized"] = peak / 32768
        result["silent"] = peak == 0
    return result


class Exporter:
    def __init__(self, db, journal, output):
        self.db = db
        self.journal = journal
        self.output = output
        self.catalog = Catalog(db)
        self.renderers = load_renderers(db)
        self.materials = {}
        self.completed = {}

    def remember(self, row, status, outputs, detail, error):
        item = {"kind": row["kind"], "file_id": row["file_id"], "path_id": row["path_id"],
                "archive": row["archive"], "logical_path": row["logical_path"], "name": row["name"],
                "status": status, "output_json": json.dumps(outputs, ensure_ascii=False),
                "detail_json": json.dumps(detail, ensure_ascii=False), "error": error,
                "updated_at": datetime.now(timezone.utc).isoformat()}
        self.journal.put(item)
        self.completed[(row["kind"], row["file_id"], row["path_id"])] = item
        return item

    def export_row(self, row):
        previous = self.journal.get(row["kind"], row["file_id"], row["path_id"])
        try:
            if row["kind"] == "texture":
                status, outputs, detail, error = self.texture(row)
            elif row["kind"] == "sprite":
                status, outputs, detail, error = self.sprite(row)
            elif row["kind"] == "audio":
                status, outputs, detail, error = self.audio(row)
            else:
                status, outputs, detail, error = self.mesh(row)
        except Exception as error_value:
            status, outputs, detail, error = "failed", [], {}, error_text(error_value)
        if status != "ok":
            for record in outputs:
                self.remove_output(record["path"])
            outputs = []
        elif previous is not None:
            current = {record["path"] for record in outputs}
            for old in json.loads(previous["output_json"] or "[]"):
                if old["path"] not in current:
                    self.remove_output(old["path"])
        detail.setdefault("source_sha256", row["sha256"])
        detail["exporter_revision"] = EXPORTER_REVISION
        return self.remember(row, status, outputs, detail, error)

    def remove_output(self, relative):
        path = self.output / relative
        if path.is_file() and not path.is_symlink() and inside(self.output, path):
            path.unlink()

    def variant_destination(self, row, suffix, variant):
        path = self.destination(row, suffix)
        if not variant:
            return path
        path = path.with_name(f"{path.stem}__{variant}{suffix}")
        if not inside(self.output, path):
            raise ValueError(f"La salida se sale del destino: {path.name}")
        return path

    def destination(self, row, suffix):
        relative = item_relative_path(row["kind"], row["archive"], row["logical_path"], row["path_id"], row["name"], suffix)
        path = self.output / relative
        if not inside(self.output, path):
            raise ValueError(f"La salida se sale del destino: {relative}")
        return path

    def save_image(self, image, path):
        image.load()
        temporary = path.with_name(path.name + ".partial")
        path.parent.mkdir(parents=True, exist_ok=True)
        image.save(temporary, format="PNG", compress_level=1)
        os.replace(temporary, path)
        with Image.open(path) as decoded:
            decoded.load()
            if decoded.size != image.size or decoded.tobytes() != image.tobytes():
                path.unlink()
                raise ValueError("El PNG no conserva la imagen decodificada")
        return file_record(self.output, path)

    def texture(self, row):
        texture = self.catalog.object(row["file_id"], row["path_id"]).parse_as_object()
        if texture.m_Width <= 0 or texture.m_Height <= 0:
            return "skipped", [], {"reason": "textura sin dimensiones"}, "textura sin dimensiones"
        image = texture.image
        if image.size != (texture.m_Width, texture.m_Height):
            raise ValueError("Dimensiones de textura incorrectas")
        path = self.destination(row, ".png")
        saved = self.save_image(image, path)
        settings = texture.m_TextureSettings
        detail = {"width": image.size[0], "height": image.size[1], "mode": image.mode,
                  "unity_format": int(texture.m_TextureFormat),
                  "filter_mode": component(settings, "m_FilterMode"),
                  "png_pixels_match_decoded_source": True, "limitations": []}
        return "ok", [saved], detail, None

    def sprite(self, row):
        reader = self.catalog.object(row["file_id"], row["path_id"])
        sprite = reader.parse_as_object()
        limitations = []
        image_error = None
        try:
            image = sprite.image
        except Exception as error:
            image = self.crop_sprite(row["file_id"], reader.parse_as_dict())
            limitations.append("tight_mesh_not_applied")
            image_error = error_text(error)
        if image.size[0] <= 0 or image.size[1] <= 0:
            return "skipped", [], {"reason": "sprite sin píxeles"}, "sprite sin píxeles"
        saved = self.save_image(image, self.destination(row, ".png"))
        detail = {"width": image.size[0], "height": image.size[1], "mode": image.mode,
                  "png_pixels_match_decoded_source": True, "limitations": limitations}
        if image_error:
            detail["sprite_image_error"] = image_error
        return "ok", [saved], detail, None

    def crop_sprite(self, owner_file_id, data):
        render = data.get("m_RD") or {}
        target = resolve_pointer(self.db, owner_file_id, render.get("texture"))
        if target is None:
            raise ValueError("El sprite no tiene textura resoluble")
        image = self.catalog.object(*target).parse_as_object().image
        image.load()
        alpha = resolve_pointer(self.db, owner_file_id, render.get("alphaTexture"))
        if alpha is not None:
            alpha_image = self.catalog.object(*alpha).parse_as_object().image.convert("L")
            image = Image.merge("RGBA", (*image.convert("RGB").split(), alpha_image))
        rect = render["textureRect"]
        cropped = image.crop((rect["x"], rect["y"], rect["x"] + rect["width"], rect["y"] + rect["height"]))
        return cropped.transpose(Image.Transpose.FLIP_TOP_BOTTOM)

    def audio(self, row):
        entry = self.catalog.asset(row["file_id"])
        stream = self.db.execute("SELECT * FROM streams WHERE owner_file=? AND object_path_id=?",
                                 (row["file_id"], row["path_id"])).fetchone()
        resource = None
        if stream is not None:
            if stream["target_file"] is None or stream["range_valid"] != 1:
                return "failed", [], {}, "Stream de audio fuera de rango o sin archivo"
            resource_row, raw = self.catalog.read_verified(stream["target_file"])
            # El recurso se registra después del serializado: su basename simplificado puede coincidir.
            entry["env"].load_file(raw, name=resource_row["logical_path"])
            resource = {"archive": resource_row["archive"], "logical_path": resource_row["logical_path"],
                        "offset": stream["offset"], "size": stream["size"], "sha256": resource_row["sha256"]}
        audio = entry["asset"].objects[row["path_id"]].parse_as_object()
        samples = audio.samples
        if not samples:
            return "failed", [], {}, "AudioClip sin muestras"
        outputs, descriptions, limitations = [], [], []
        for index, (label, data) in enumerate(samples.items()):
            suffix = PurePosixPath(str(label)).suffix.lower()
            if suffix not in AUDIO_EXTENSIONS:
                suffix = ".bin"
                limitations.append("contenedor_no_reconocido")
            path = self.destination(row, suffix)
            if index:
                path = path.with_name(f"{path.stem}__{index}{suffix}")
            publish(path, data)
            info = {"source_name": str(label), "bytes": len(data)}
            if suffix == ".wav":
                try:
                    info.update(describe_wav(data))
                except Exception as error:
                    path.unlink()
                    return "failed", outputs, {}, error_text(error)
                if info.get("silent"):
                    limitations.append("silent")
                if info.get("channels") != audio.m_Channels or info.get("sample_rate") != audio.m_Frequency:
                    limitations.append("metadata_differs")
                duration = info.get("duration_seconds")
                if duration is not None and audio.m_Frequency:
                    if abs(duration - float(audio.m_Length)) > max(1 / audio.m_Frequency, 0.05):
                        limitations.append("duration_differs")
            descriptions.append(info)
            outputs.append(file_record(self.output, path))
        detail = {"samples": descriptions, "channels": audio.m_Channels, "frequency": audio.m_Frequency,
                  "metadata_duration_seconds": audio.m_Length, "resource": resource, "limitations": limitations}
        return "ok", outputs, detail, None

    def material(self, file_id, path_id):
        key = (file_id, path_id)
        if key not in self.materials:
            reader = self.catalog.object(file_id, path_id)
            if reader.type.name != "Material":
                raise ValueError("La referencia de material no apunta a un Material")
            data = reader.parse_as_dict()
            saved = data.get("m_SavedProperties") or {}
            texenvs = property_map(saved.get("m_TexEnvs") or [])
            colors = property_map(saved.get("m_Colors") or [])
            limitations, texture, scale, offset = [], None, (1.0, 1.0), (0.0, 0.0)
            if "_MainTex" in texenvs:
                texenv = texenvs["_MainTex"]
                scale = vec2(component(texenv, "m_Scale"))
                offset = vec2(component(texenv, "m_Offset"))
                pointer = component(texenv, "m_Texture")
                texture = resolve_pointer(self.db, file_id, pointer)
                if texture is None and component(pointer, "m_PathID"):
                    limitations.append("texture_unresolved")
            else:
                limitations.append("no_main_texture")
            if not near(scale, (1.0, 1.0)):
                limitations.append("uv_scale")
            if not near(offset, (0.0, 0.0)):
                limitations.append("uv_offset")
            self.materials[key] = {"name": data.get("m_Name") or "unnamed", "tint": rgba(colors.get("_Color")),
                                   "texture": texture, "scale": scale, "offset": offset, "limitations": limitations}
        return self.materials[key]

    def ensure_texture(self, file_id, path_id):
        key = ("texture", file_id, path_id)
        known = self.completed.get(key)
        if known is not None and known["status"] != "failed":
            return json.loads(known["output_json"]) if known["status"] == "ok" else None
        record = self.journal.get("texture", file_id, path_id)
        if record is not None and decide(record, self.output) == "skip":
            self.completed[key] = dict(record)
            return json.loads(record["output_json"]) if record["status"] == "ok" else None
        row = self.db.execute("""
            SELECT o.file_id, o.path_id, o.type, o.name, o.details_json, f.archive, f.logical_path, f.sha256
            FROM objects o JOIN files f ON f.id=o.file_id
            WHERE o.file_id=? AND o.path_id=? AND o.type='Texture2D'
        """, (file_id, path_id)).fetchone()
        if row is None:
            return None
        item = self.export_row(dict(row, kind="texture"))
        if item["status"] != "ok":
            return None
        return json.loads(item["output_json"])

    def mesh(self, row):
        reader = self.catalog.object(row["file_id"], row["path_id"])
        mesh = reader.parse_as_object()
        handler = MeshHandler(mesh)
        handler.process()
        vertices = list(handler.m_Vertices or [])
        if handler.m_VertexCount <= 0 or not vertices:
            return "skipped", [], {"reason": "malla sin vértices"}, "malla sin vértices"
        submeshes = list(handler.get_triangles() or [])
        if not any(submeshes):
            return "skipped", [], {"reason": "malla sin triángulos"}, "malla sin triángulos"
        renderers = self.renderers.get((row["file_id"], row["path_id"]), [])
        groups = ordered_groups(renderers, row["file_id"], len(submeshes))
        chosen_renderers = [min(group, key=lambda renderer: (
            renderer["file_id"] != row["file_id"], renderer["file_id"], renderer["path_id"])) for group in groups]
        if not chosen_renderers:
            chosen_renderers = [None]
        limitations = []
        if chosen_renderers == [None]:
            limitations.append("no_renderer")
        if len(groups) > 1:
            limitations.append("multiple_material_assignments")
        stem = safe_stem(row["name"])
        uv_source, normal_source = list(handler.m_UV0 or []), list(handler.m_Normals or [])
        outputs, variants, info = [], [], None
        for index, chosen in enumerate(chosen_renderers):
            label = None if len(chosen_renderers) == 1 or index == 0 else f"{chosen['file_id']}_{chosen['path_id']}"
            obj_path = self.variant_destination(row, ".obj", label)
            mtl_path = self.variant_destination(row, ".mtl", label)
            material_names, material_details, material_limits = self.bind_materials(
                chosen, submeshes, mtl_path)
            limitations.extend(material_limits)
            text, positions, uvs, normals, info = build_obj(
                stem, mtl_path.name, vertices, uv_source, normal_source, submeshes, material_names)
            check_obj_text(text, positions, uvs, normals, submeshes)
            publish(obj_path, text)
            publish(mtl_path, mtl_document(material_details))
            obj_record, mtl_record = file_record(self.output, obj_path), file_record(self.output, mtl_path)
            outputs.extend((obj_record, mtl_record))
            variants.append({"label": label or obj_path.stem, "preferred": index == 0,
                             "renderer": None if chosen is None else {"type": chosen["type"],
                             "file_id": chosen["file_id"], "path_id": chosen["path_id"]},
                             "obj": obj_record["path"], "mtl": mtl_record["path"], "materials": material_details})
        if info["non_finite_replaced"]:
            limitations.append("non_finite_coordinates_replaced")
        if not info["uv_exported"]:
            limitations.append("no_uv")
        if not info["normals_exported"]:
            limitations.append("no_normals")
        bind_poses = len(getattr(mesh, "m_BindPose", None) or [])
        if bind_poses:
            limitations.append("rest_pose_only")
        if handler.m_Colors:
            limitations.append("vertex_colors_not_exported")
        preferred = variants[0]
        detail = {**info, "submeshes": len(submeshes), "bind_poses": bind_poses,
                  "vertex_colors_present": bool(handler.m_Colors), "vertex_colors_exported": False,
                  "skeleton_and_animations_exported": False,
                  "material_assignment": "missing" if preferred["renderer"] is None else
                  "unique" if len(groups) <= 1 else "multiple",
                  "renderer_count": len(renderers), "renderer": preferred["renderer"],
                  "materials": preferred["materials"], "variants": variants,
                  "geometry_matches_source": True,
                  "coordinate_conversion": "X reflected, triangle winding reversed, UV unchanged",
                  "original_shader_not_reproduced": True,
                  "limitations": sorted(set(limitations))}
        return "ok", outputs, detail, None

    def bind_materials(self, chosen, submeshes, mtl_path):
        slots = list(chosen["slots"]) if chosen else []
        while len(slots) < len(submeshes):
            slots.append(None)
        names, details, limitations = [], [], []
        if chosen and len(chosen["slots"]) != len(submeshes):
            limitations.append("material_slot_mismatch")
        for index, slot in enumerate(slots[:len(submeshes)]):
            map_path = None
            placeholder = f"unassigned_{index}"
            if slot is None or slot["resolution"] != "resolved" or slot["target_file"] is None:
                names.append(placeholder)
                details.append({"index": index, "assigned": False, "mtl_name": placeholder, "tint_rgba": (1, 1, 1, 1)})
                if chosen:
                    limitations.append("material_unresolved")
                continue
            try:
                view = self.material(slot["target_file"], slot["target_path_id"])
            except Exception as error:
                names.append(placeholder)
                details.append({"index": index, "assigned": False, "mtl_name": placeholder, "tint_rgba": (1, 1, 1, 1),
                                "error": error_text(error)})
                limitations.append("material_unreadable")
                continue
            limitations.extend(view["limitations"])
            mtl_name = f"m{slot['target_path_id']}_{safe_stem(view['name'])}"
            names.append(mtl_name)
            if view["texture"] is not None:
                texture_record = self.ensure_texture(*view["texture"])
                if texture_record:
                    map_path = relative_reference(mtl_path, self.output / texture_record[0]["path"])
                    if (mtl_path.parent / map_path).resolve() != (self.output / texture_record[0]["path"]).resolve():
                        raise ValueError("map_Kd no apunta a la textura exportada")
                else:
                    limitations.append("texture_not_exported")
            details.append({
                "index": index, "assigned": True, "mtl_name": mtl_name, "name": view["name"],
                "material_file_id": slot["target_file"], "material_path_id": slot["target_path_id"],
                "tint_rgba": view["tint"], "uv_scale": view["scale"], "uv_offset": view["offset"],
                "texture": None if view["texture"] is None else {"file_id": view["texture"][0], "path_id": view["texture"][1]},
                "map_kd": map_path})
        return names, details, limitations


def mtl_document(materials):
    lines = ["# Textura difusa y tinte. No reproduce el shader original."]
    seen = set()
    for material in materials:
        name = material.get("mtl_name")
        if not name or name in seen:
            continue
        seen.add(name)
        red, green, blue, alpha = material.get("tint_rgba") or (1, 1, 1, 1)
        lines.extend([f"newmtl {name}", "Ka 0 0 0", f"Kd {red:.9g} {green:.9g} {blue:.9g}",
                      "Ks 0 0 0", f"d {alpha:.9g}", "illum 1"])
        if material.get("map_kd"):
            options = ""
            scale, offset = material.get("uv_scale") or (1, 1), material.get("uv_offset") or (0, 0)
            if not near(tuple(scale), (1.0, 1.0)):
                options += f" -s {scale[0]:.9g} {scale[1]:.9g} 1"
            if not near(tuple(offset), (0.0, 0.0)):
                options += f" -o {offset[0]:.9g} {offset[1]:.9g} 0"
            lines.append(f"map_Kd{options} {material['map_kd']}")
    return "\n".join(lines) + "\n"


def summarize(journal, output, originals, profile, started, this_run):
    counts, limitations, reasons = Counter(), Counter(), Counter()
    recovered = failed = 0
    for row in journal.rows():
        counts[(row["kind"], row["status"])] += 1
        if row["status"] == "ok":
            recovered += 1
        elif row["status"] == "failed":
            failed += 1
            reasons[row["error"] or "sin mensaje"] += 1
        else:
            reasons[row["error"] or "omitido"] += 1
        detail = json.loads(row["detail_json"] or "{}")
        for limitation in detail.get("limitations") or []:
            if not limitation.startswith(("AssertionError", "ValueError", "TypeError", "RuntimeError")):
                limitations[limitation.split(":", 1)[0]] += 1
    by_kind = {kind: {status: counts[(kind, status)] for status in ("ok", "failed", "skipped")}
               for kind in KIND_TYPES}
    bytes_written = 0
    files = 0
    for path in output.rglob("*"):
        if not path.is_file() or path.is_symlink() or path.name in {"summary.json", "failures.jsonl", "README.md", "journal.sqlite"}:
            continue
        if path.suffix in {".png", ".obj", ".mtl", ".wav", ".ogg", ".m4a", ".bin"}:
            bytes_written += path.stat().st_size
            files += 1
    mismatched = []
    for row in journal.rows():
        if row["status"] != "ok":
            continue
        if not outputs_match(output, json.loads(row["output_json"] or "[]")):
            mismatched.append({"kind": row["kind"], "file_id": row["file_id"], "path_id": row["path_id"]})
    status = "completed_with_failures" if failed else "completed"
    if profile == "trial":
        status = "trial_" + status
    if mismatched:
        status = "inconsistent"
    return {"schema_version": 1, "status": status, "profile": profile,
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "started_at_utc": started, "unitypy": version("UnityPy"), "pillow": version("Pillow"),
            "items": by_kind, "recovered_items": recovered, "failed_items": failed,
            "output_files": files, "output_bytes": bytes_written,
            "this_run": this_run, "skip_and_failure_reasons": reasons.most_common(30),
            "limitations": limitations.most_common(), "outputs_rechecked": not mismatched,
            "mismatched_items": mismatched[:20], "original_sha256": originals,
            "original_hashes_rechecked": True,
            "notes": ["Los nombres repetidos se distinguen con paquete, ruta de origen y path_id.",
                      "Una reanudación no repite un item ok cuyo archivo conserva el SHA256.",
                      "Los items fallidos se reintentan. Los omitidos de forma determinista, no.",
                      "No se exportan esqueletos, pesos, animaciones, cubemaps ni fuentes.",
                      "El MTL guarda tinte y textura principal. El shader original no se reproduce.",
                      "La escala y el desplazamiento de UV van en map_Kd; hay visores que los ignoran."]}


def write_reports(journal, output, summary):
    (output / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    with (output / "failures.jsonl").open("w") as handle:
        for row in journal.rows():
            if row["status"] == "failed":
                handle.write(json.dumps({"kind": row["kind"], "archive": row["archive"],
                                         "logical_path": row["logical_path"], "file_id": row["file_id"],
                                         "path_id": row["path_id"], "name": row["name"], "error": row["error"]},
                                        ensure_ascii=False) + "\n")
    counts = summary["items"]
    lines = ["# Extracción masiva", "",
             "Texturas PNG, sprites PNG, mallas OBJ/MTL y sonidos. Sin esqueletos ni animaciones.",
             "Cada nombre lleva el path_id y vive bajo el paquete y la ruta de origen, así que un nombre repetido no pisa a otro.",
             "",
             "| Tipo | Recuperados | Fallidos | Omitidos |",
             "| --- | ---: | ---: | ---: |"]
    labels = {"texture": "Texturas", "sprite": "Sprites", "audio": "Sonidos", "mesh": "Mallas"}
    for kind, label in labels.items():
        item = counts[kind]
        lines.append(f"| {label} | {item['ok']} | {item['failed']} | {item['skipped']} |")
    lines.extend(["", "El diario está en `journal.sqlite`. Los fallos, en `failures.jsonl`. El resumen, en `summary.json`.",
                  "Volver a ejecutar la misma orden continúa sin repetir lo ya comprobado.", ""])
    (output / "README.md").write_text("\n".join(lines))


def export_bulk(output, profile="all", limit=0, kinds=None):
    kinds = set(kinds or KIND_TYPES)
    unknown = kinds - set(KIND_TYPES)
    if unknown or profile not in {"trial", "all"}:
        raise ValueError(f"Selección no válida: {profile} {sorted(kinds)}")
    output = prepare_output(Path(output))
    cleanup_partials(output)
    started = datetime.now(timezone.utc).isoformat()
    originals = original_hashes()
    assert_originals(originals)
    journal = Journal(output / "journal.sqlite")
    db = sqlite3.connect((ROOT / "work/inventory/resources.sqlite").as_uri() + "?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    try:
        rows = load_catalog(db)
        work = select_work(rows, journal, output, profile, limit, kinds)
        print(f"Recursos pendientes en esta ejecución: {len(work)}", flush=True)
        exporter = Exporter(db, journal, output)
        this_run = Counter()
        for index, row in enumerate(work, 1):
            item = exporter.export_row(row)
            this_run[item["status"]] += 1
            if item["status"] == "failed" or len(work) <= 40 or index % 100 == 0 or index == len(work):
                print(f"{index}/{len(work)} {item['status']} {row['kind']} {row['name']}", flush=True)
        assert_originals(originals)
        summary = summarize(journal, output, originals, profile, started, dict(this_run))
        write_reports(journal, output, summary)
    finally:
        db.close()
        journal.close()
    print(f"Extracción {summary['status']}: {output}", flush=True)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "exports/bulk")
    parser.add_argument("--profile", choices=("trial", "all"), default="all")
    parser.add_argument("--limit", type=int, default=0, help="Máximo de cada tipo; 0 exporta todos los pendientes")
    parser.add_argument("--kinds", default="texture,sprite,audio,mesh")
    args = parser.parse_args()
    if args.limit < 0:
        raise SystemExit("El límite no puede ser negativo")
    summary = export_bulk(args.output, args.profile, args.limit, [kind for kind in args.kinds.split(",") if kind])
    if summary["status"] == "inconsistent":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
