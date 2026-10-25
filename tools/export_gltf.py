"""Convierte los OBJ de la extracción masiva a glTF 2.0 binario (.glb).

Solo entiende el OBJ que escribió tools.export_bulk: triángulos, el mismo índice
para posición, UV y normal, y un MTL con Kd, d y map_Kd. Las posiciones y las
normales se copian tal cual (el OBJ ya está en Y hacia arriba con X reflejada).
La única transformación es la V de las UV, porque OBJ/Unity cuentan desde abajo y
glTF desde arriba. La textura PNG solo se referencia, no se copia ni se incrusta.
Se puede reanudar: un OBJ cuyo SHA256, y el del GLB, coinciden con el diario no
se repite.

    uv run --locked -m tools.export_gltf --output exports/gltf
"""

import argparse
from array import array
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path, PurePosixPath
import sqlite3
import struct
import sys
from urllib.parse import quote

from tools.prepare_assets import sha256_file

ROOT = Path(__file__).resolve().parents[1]
CONVERTER_REVISION = 4
GENERATOR = "pixelgun3d export_gltf"
RESERVED = ("exports/bulk", "exports/samples", "exports/samples-weapon", "work")
UINT16_LIMIT = 65536
NEAREST, LINEAR = 9728, 9729
GLB_MAGIC, GLB_VERSION, CHUNK_JSON, CHUNK_BIN = 0x46546C67, 2, 0x4E4F534A, 0x004E4942
ARRAY_BUFFER, ELEMENT_ARRAY_BUFFER = 34962, 34963
FLOAT, UNSIGNED_SHORT, UNSIGNED_INT = 5126, 5123, 5125
IDENTITY_TOLERANCE = 1e-5
NORMAL_TOLERANCE = 6e-3  # el validador de glTF admite ~6,7e-3

assert array("f").itemsize == 4 and array("H").itemsize == 2 and array("I").itemsize == 4


class ConversionError(ValueError):
    """El OBJ o el MTL no tienen la forma que escribe la extracción."""


def error_text(error):
    text = f"{type(error).__name__}: {error}"
    return text if len(text) <= 500 else text[:497] + "..."


def inside(root, path):
    resolved, base = Path(path).resolve(), Path(root).resolve()
    return resolved == base or base in resolved.parents


def little(values):
    """Bytes little-endian de un array de 'f', 'H' o 'I'."""
    if sys.byteorder == "big":
        values = array(values.typecode, values)
        values.byteswap()
    return values.tobytes()


# ---------------------------------------------------------------- lectura

def parse_obj(path):
    """Devuelve posiciones, uv, normales (arrays planos) y grupos [(material, índices)]."""
    positions, uvs, normals = [], [], []
    groups = []
    current = None
    face_slashes = None
    stride = 0
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        if not line or line[0] == "#":
            continue
        head, _, rest = line.partition(" ")
        if head == "v" or head == "vn":
            parts = rest.split()
            if len(parts) != 3:
                raise ConversionError(f"línea {number}: {head} sin tres componentes")
            (positions if head == "v" else normals).extend(parts)
        elif head == "vt":
            parts = rest.split()
            if len(parts) != 2:
                raise ConversionError(f"línea {number}: vt sin dos componentes")
            uvs.extend(parts)
        elif head == "f":
            if face_slashes is None:
                if len(positions) % 3 or not positions:
                    raise ConversionError("caras sin posiciones")
                has_uv, has_normals = bool(uvs), bool(normals)
                face_slashes = 2 if has_normals else 1 if has_uv else 0
                stride = 1 + has_uv + has_normals
            if rest.count("/") != 3 * face_slashes:
                raise ConversionError(f"línea {number}: forma de cara inesperada")
            tokens = rest.replace("/", " ").split()
            if len(tokens) != 3 * stride:
                raise ConversionError(f"línea {number}: la cara no es un triángulo")
            first = tokens[0::stride]
            for offset in range(1, stride):
                if tokens[offset::stride] != first:
                    raise ConversionError(f"línea {number}: índices distintos para posición, UV o normal")
            if current is None:
                current = [None, []]
                groups.append(current)
            current[1].extend(first)
        elif head == "g":
            current = [None, []]
            groups.append(current)
        elif head == "usemtl":
            if current is None or current[1]:
                current = [None, []]
                groups.append(current)
            current[0] = rest.strip()
        elif head in ("mtllib", "o", "s"):
            continue
        else:
            raise ConversionError(f"línea {number}: instrucción no admitida {head!r}")
    vertex_count = len(positions) // 3
    if not vertex_count or len(positions) % 3:
        raise ConversionError("OBJ sin vértices")
    if len(uvs) % 2 or (uvs and len(uvs) // 2 != vertex_count):
        raise ConversionError("las UV no coinciden con los vértices")
    if len(normals) % 3 or (normals and len(normals) // 3 != vertex_count):
        raise ConversionError("las normales no coinciden con los vértices")
    result = []
    for material, indices in groups:
        if not indices:
            continue
        values = array("I", [int(token) - 1 for token in indices])
        if min(values) < 0 or max(values) >= vertex_count:
            raise ConversionError("índice de malla fuera de rango")
        result.append((material, values))
    if not result:
        raise ConversionError("OBJ sin triángulos")
    return array("f", map(float, positions)), array("f", map(float, uvs)), array("f", map(float, normals)), result


def mtllib_name(path):
    for line in Path(path).read_text().splitlines():
        if line.startswith("mtllib "):
            return line[7:].strip()
    return None


def parse_mtl(path, exports_root):
    """{nombre: {"kd": (r,g,b), "d": float, "map": {"png": Path, "scale", "offset"} | None}}"""
    materials, current = {}, None
    for number, line in enumerate(Path(path).read_text().splitlines(), 1):
        parts = line.split()
        if not parts or parts[0] == "#" or parts[0].startswith("#"):
            continue
        key = parts[0]
        if key == "newmtl":
            if len(parts) != 2:
                raise ConversionError(f"MTL línea {number}: nombre de material no válido")
            current = {"kd": (1.0, 1.0, 1.0), "d": 1.0, "map": None}
            materials[parts[1]] = current
        elif current is None:
            raise ConversionError(f"MTL línea {number}: dato antes de newmtl")
        elif key == "Kd":
            current["kd"] = tuple(float(value) for value in parts[1:4])
            if len(parts) != 4:
                raise ConversionError(f"MTL línea {number}: Kd sin tres componentes")
        elif key == "d":
            current["d"] = float(parts[1])
        elif key in ("Ka", "Ks", "illum"):
            continue
        elif key == "map_Kd":
            scale, offset, index = (1.0, 1.0), (0.0, 0.0), 1
            while index < len(parts) and parts[index].startswith("-"):
                option = parts[index]
                if option not in ("-s", "-o") or index + 3 >= len(parts):
                    raise ConversionError(f"MTL línea {number}: opción {option} no admitida")
                x, y = float(parts[index + 1]), float(parts[index + 2])
                if option == "-s":
                    scale = (x, y)
                else:
                    offset = (x, y)
                index += 4
            name = " ".join(parts[index:])
            if not name:
                raise ConversionError(f"MTL línea {number}: map_Kd sin ruta")
            png = (Path(path).parent / name).resolve()
            if not inside(exports_root, png) or PurePosixPath(name).is_absolute():
                raise ConversionError(f"la textura se sale de exports/: {name}")
            current["map"] = {"png": png, "scale": scale, "offset": offset}
        else:
            raise ConversionError(f"MTL línea {number}: instrucción no admitida {key!r}")
    return materials


# ---------------------------------------------------------------- escritura

def unit_normals(normals):
    """Normales de longitud 1. Unity las guarda cuantizadas y algunas quedan hasta un 1 % cortas.

    Solo se toca un vector que se aparta de 1 más que la tolerancia; los demás se copian
    igual. Devuelve (normales, cuántos se corrigieron). Un vector nulo no se puede corregir.
    """
    fixed, count = array("f", normals), 0
    for start in range(0, len(fixed), 3):
        x, y, z = fixed[start:start + 3]
        length = math.sqrt(x * x + y * y + z * z)
        if length and abs(length - 1.0) > NORMAL_TOLERANCE:
            fixed[start:start + 3] = array("f", (x / length, y / length, z / length))
            count += 1
    return fixed, count


def near(pair, origin):
    return all(abs(a - b) <= IDENTITY_TOLERANCE for a, b in zip(pair, origin))


def pad4(data, fill=b"\0"):
    return data + fill * (-len(data) % 4)


def reference(glb_path, png):
    relative = os.path.relpath(png, Path(glb_path).parent)
    return quote(Path(relative).as_posix(), safe="/")


def build_glb(stem, glb_path, positions, uvs, normals, groups, materials, exports_root, filter_modes):
    """Devuelve los bytes del GLB y el detalle de lo que contiene."""
    vertex_count = len(positions) // 3
    use_uv, use_normals = bool(uvs), bool(normals)
    binary = bytearray()
    views, accessors = [], []

    def add_view(data, target):
        binary.extend(b"\0" * (-len(binary) % 4))
        views.append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(data), "target": target})
        binary.extend(data)
        return len(views) - 1

    def add_accessor(view, component, count, kind, **extra):
        accessors.append({"bufferView": view, "componentType": component, "count": count, "type": kind, **extra})
        return len(accessors) - 1

    attributes = {"POSITION": add_accessor(
        add_view(little(positions), ARRAY_BUFFER), FLOAT, vertex_count, "VEC3",
        min=[min(positions[axis::3]) for axis in range(3)], max=[max(positions[axis::3]) for axis in range(3)])}
    renormalized = 0
    if use_normals:
        normals, renormalized = unit_normals(normals)
        attributes["NORMAL"] = add_accessor(add_view(little(normals), ARRAY_BUFFER), FLOAT, vertex_count, "VEC3")
    if use_uv:
        flipped = array("f", uvs)
        flipped[1::2] = array("f", (1.0 - value for value in uvs[1::2]))
        attributes["TEXCOORD_0"] = add_accessor(add_view(little(flipped), ARRAY_BUFFER), FLOAT, vertex_count, "VEC2")

    index_type, index_code = (UNSIGNED_SHORT, "H") if vertex_count < UINT16_LIMIT else (UNSIGNED_INT, "I")
    gltf_materials, material_ids = [], {}
    images, image_ids, samplers, sampler_ids, textures, texture_ids = [], {}, [], {}, [], {}
    details = {"textures": [], "alpha_blend": 0, "uv_transform": 0, "ignored_textures": 0}
    primitives = []

    def material_for(name):
        if name in material_ids:
            return material_ids[name]
        if name not in materials:
            raise ConversionError(f"usemtl {name!r} no está en el MTL")
        source = materials[name]
        red, green, blue = source["kd"]
        alpha = source["d"]
        pbr = {"baseColorFactor": [red, green, blue, alpha], "metallicFactor": 0.0, "roughnessFactor": 1.0}
        material = {"name": name, "pbrMetallicRoughness": pbr, "doubleSided": False}
        if alpha < 1.0:
            material["alphaMode"] = "BLEND"
            details["alpha_blend"] += 1
        texture = source["map"]
        if texture and not use_uv:
            details["ignored_textures"] += 1
        elif texture:
            png = texture["png"]
            if not png.is_file() or png.is_symlink():
                raise ConversionError(f"la textura no existe: {png}")
            uri = reference(glb_path, png)
            nearest = filter_modes.get(png.resolve().relative_to(Path(exports_root).resolve()).as_posix()) == 0
            if uri not in image_ids:
                image_ids[uri] = len(images)
                images.append({"uri": uri})
            if nearest not in sampler_ids:
                sampler_ids[nearest] = len(samplers)
                filter_value = NEAREST if nearest else LINEAR
                samplers.append({"magFilter": filter_value, "minFilter": filter_value})
            key = (uri, nearest)
            if key not in texture_ids:
                texture_ids[key] = len(textures)
                textures.append({"source": image_ids[uri], "sampler": sampler_ids[nearest]})
            info = {"index": texture_ids[key], "texCoord": 0}
            (scale_x, scale_y), (offset_x, offset_y) = texture["scale"], texture["offset"]
            if not (near((scale_x, scale_y), (1.0, 1.0)) and near((offset_x, offset_y), (0.0, 0.0))):
                # La UV de Unity crece hacia arriba; la de glTF, hacia abajo: v' = 1 - v.
                info["extensions"] = {"KHR_texture_transform": {
                    "scale": [scale_x, scale_y], "offset": [offset_x, 1.0 - scale_y - offset_y]}}
                details["uv_transform"] += 1
            pbr["baseColorTexture"] = info
            details["textures"].append(uri)
        material_ids[name] = len(gltf_materials)
        gltf_materials.append(material)
        return material_ids[name]

    triangles = 0
    for name, indices in groups:
        triangles += len(indices) // 3
        data = indices if index_code == "I" else array("H", indices)
        view = add_view(little(data), ELEMENT_ARRAY_BUFFER)
        primitive = {"attributes": dict(attributes), "indices": add_accessor(view, index_type, len(indices), "SCALAR"),
                     "mode": 4}
        if name is not None:
            primitive["material"] = material_for(name)
        primitives.append(primitive)

    binary.extend(b"\0" * (-len(binary) % 4))
    document = {
        "asset": {"version": "2.0", "generator": GENERATOR},
        "scene": 0, "scenes": [{"nodes": [0]}],
        "nodes": [{"name": stem, "mesh": 0}],
        "meshes": [{"name": stem, "primitives": primitives}],
        "accessors": accessors, "bufferViews": views,
        "buffers": [{"byteLength": len(binary)}],
    }
    if gltf_materials:
        document["materials"] = gltf_materials
    if images:
        document.update(images=images, samplers=samplers, textures=textures)
    if details["uv_transform"]:
        document["extensionsUsed"] = ["KHR_texture_transform"]
    body = pad4(json.dumps(document, separators=(",", ":")).encode(), b" ")
    payload = pad4(bytes(binary))
    total = 12 + 8 + len(body) + 8 + len(payload)
    glb = (struct.pack("<III", GLB_MAGIC, GLB_VERSION, total)
           + struct.pack("<II", len(body), CHUNK_JSON) + body
           + struct.pack("<II", len(payload), CHUNK_BIN) + payload)
    details.update(vertices=vertex_count, triangles=triangles, primitives=len(primitives),
                   materials=len(gltf_materials), uv=use_uv, normals=use_normals, normals_renormalized=renormalized,
                   index_type="uint16" if index_code == "H" else "uint32", size_bytes=len(glb))
    return glb, details


def convert_obj(obj_path, glb_path, exports_root, filter_modes):
    """Lee el OBJ y su MTL y devuelve (bytes del GLB, detalle). No escribe nada."""
    obj_path = Path(obj_path)
    positions, uvs, normals, groups = parse_obj(obj_path)
    name = mtllib_name(obj_path)
    materials = {}
    if name:
        mtl = (obj_path.parent / name).resolve()
        if not inside(obj_path.parent, mtl) or not mtl.is_file():
            raise ConversionError(f"MTL no usable: {name}")
        materials = parse_mtl(mtl, exports_root)
    elif any(material for material, _ in groups):
        raise ConversionError("usemtl sin mtllib")
    return build_glb(obj_path.stem, glb_path, positions, uvs, normals, groups, materials, exports_root, filter_modes)


# ---------------------------------------------------------------- relectura

def read_glb(path):
    """(documento JSON, bytes BIN) de un GLB. Rechaza cabeceras o chunks mal alineados."""
    data = Path(path).read_bytes()
    magic, version, length = struct.unpack_from("<III", data, 0)
    if magic != GLB_MAGIC or version != GLB_VERSION or length != len(data):
        raise ConversionError("cabecera GLB incorrecta")
    offset, chunks = 12, {}
    while offset < length:
        size, kind = struct.unpack_from("<II", data, offset)
        if size % 4:
            raise ConversionError("chunk GLB sin alinear a 4 bytes")
        chunks[kind] = data[offset + 8:offset + 8 + size]
        offset += 8 + size
    return json.loads(chunks[CHUNK_JSON]), chunks.get(CHUNK_BIN, b"")


def accessor_values(document, binary, index):
    """Valores planos de un accessor sin normalizar (float, uint16 o uint32)."""
    accessor = document["accessors"][index]
    view = document["bufferViews"][accessor["bufferView"]]
    code = {FLOAT: "f", UNSIGNED_SHORT: "H", UNSIGNED_INT: "I"}[accessor["componentType"]]
    width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3}[accessor["type"]]
    start = view["byteOffset"] + accessor.get("byteOffset", 0)
    values = array(code)
    values.frombytes(binary[start:start + accessor["count"] * width * values.itemsize])
    if sys.byteorder == "big":
        values.byteswap()
    return values


# ---------------------------------------------------------------- lote

def destination(models_root, output, obj_path):
    relative = Path(obj_path).resolve().relative_to(Path(models_root).resolve())
    return Path(output) / relative.with_suffix(".glb")


def load_filter_modes(source, exports_root):
    """{ruta del PNG relativa a exports/: filter_mode} desde el diario de la extracción."""
    path = Path(source) / "journal.sqlite"
    modes = {}
    if not path.is_file():
        return modes
    db = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        for output_json, detail_json in db.execute(
                "SELECT output_json, detail_json FROM items WHERE kind='texture' AND status='ok'"):
            mode = json.loads(detail_json or "{}").get("filter_mode")
            for record in json.loads(output_json or "[]"):
                png = (Path(source) / record["path"]).resolve()
                if inside(exports_root, png):
                    modes[png.relative_to(Path(exports_root).resolve()).as_posix()] = mode
    finally:
        db.close()
    return modes


SHARED = {}


def init_worker(exports_root, filter_modes):
    SHARED.update(exports_root=Path(exports_root), filter_modes=filter_modes)


def work_item(task):
    """Proceso hijo: decide si repite y convierte. No toca el diario."""
    obj_path, glb_path, previous = Path(task[0]), Path(task[1]), task[2]
    exports_root, filter_modes = SHARED["exports_root"], SHARED["filter_modes"]
    result = {"obj": obj_path.as_posix(), "glb": glb_path.as_posix()}
    try:
        obj_hash = sha256_file(obj_path)
        name = mtllib_name(obj_path)
        mtl_hash = sha256_file(obj_path.parent / name) if name and (obj_path.parent / name).is_file() else None
        result.update(obj_sha256=obj_hash, mtl_sha256=mtl_hash)
        if (previous and previous["status"] == "ok" and previous["obj_sha256"] == obj_hash
                and previous["mtl_sha256"] == mtl_hash and previous["revision"] == CONVERTER_REVISION
                and glb_path.is_file() and sha256_file(glb_path) == previous["glb_sha256"]):
            result.update(status="skipped", glb_sha256=previous["glb_sha256"],
                          glb_size=glb_path.stat().st_size, detail=previous["detail_json"])
            return result
        glb, detail = convert_obj(obj_path, glb_path, exports_root, filter_modes)
        glb_path.parent.mkdir(parents=True, exist_ok=True)
        partial = glb_path.with_name(glb_path.name + ".partial")
        partial.write_bytes(glb)
        os.replace(partial, glb_path)
        result.update(status="ok", glb_sha256=sha256_file(glb_path), glb_size=len(glb),
                      detail=json.dumps(detail, sort_keys=True))
    except Exception as error:  # el lote sigue; el fallo queda anotado
        if glb_path.exists():
            glb_path.unlink()
        result.update(status="failed", error=error_text(error))
    return result


class Journal:
    def __init__(self, path):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS models (
                obj_path TEXT PRIMARY KEY, glb_path TEXT NOT NULL, status TEXT NOT NULL,
                obj_sha256 TEXT, mtl_sha256 TEXT, glb_sha256 TEXT, glb_size INTEGER,
                detail_json TEXT, error TEXT, revision INTEGER NOT NULL, updated_at TEXT NOT NULL);
        """)
        self.db.commit()

    def previous(self):
        return {row["obj_path"]: dict(row) for row in self.db.execute("SELECT * FROM models")}

    def put(self, obj_path, glb_path, result):
        self.db.execute("""
            INSERT INTO models VALUES(:obj_path,:glb_path,:status,:obj_sha256,:mtl_sha256,:glb_sha256,
                                      :glb_size,:detail_json,:error,:revision,:updated_at)
            ON CONFLICT(obj_path) DO UPDATE SET glb_path=excluded.glb_path, status=excluded.status,
                obj_sha256=excluded.obj_sha256, mtl_sha256=excluded.mtl_sha256,
                glb_sha256=excluded.glb_sha256, glb_size=excluded.glb_size,
                detail_json=excluded.detail_json, error=excluded.error, revision=excluded.revision,
                updated_at=excluded.updated_at
        """, {"obj_path": obj_path, "glb_path": glb_path,
              "status": "ok" if result["status"] == "skipped" else result["status"],
              "obj_sha256": result.get("obj_sha256"), "mtl_sha256": result.get("mtl_sha256"),
              "glb_sha256": result.get("glb_sha256"), "glb_size": result.get("glb_size"),
              "detail_json": result.get("detail"), "error": result.get("error"),
              "revision": CONVERTER_REVISION, "updated_at": datetime.now(timezone.utc).isoformat()})

    def commit(self):
        self.db.commit()

    def close(self):
        self.db.close()


def prepare_output(output, root=ROOT):
    output, root = Path(output).resolve(), Path(root).resolve()
    if output == root or root not in output.parents:
        raise ValueError(f"El destino tiene que estar dentro del proyecto: {output}")
    for relative in RESERVED:
        reserved = (root / relative).resolve()
        if output == reserved or reserved in output.parents or output in reserved.parents:
            raise ValueError(f"Destino reservado: {output}")
    output.mkdir(parents=True, exist_ok=True)
    if not (output / "journal.sqlite").exists() and any(output.iterdir()):
        raise FileExistsError(f"El destino no tiene diario y no se va a mezclar: {output}")
    return output


def list_objs(models_root, only=None):
    objs = sorted(Path(models_root).rglob("*.obj"))
    if only:
        wanted = {Path(item).resolve() for item in only}
        wanted |= {(Path(models_root) / item).resolve() for item in only}
        objs = [obj for obj in objs if obj.resolve() in wanted]
    return objs


def verify(output, models_root, exports_root, objs=None):
    """Cuenta GLB, archivos a medias y texturas que no existen. Solo lee."""
    output = Path(output)
    objs = objs if objs is not None else list_objs(models_root)
    missing, bad_textures, textures = [], [], set()
    for obj in objs:
        glb = destination(models_root, output, obj)
        if not glb.is_file():
            missing.append(glb.as_posix())
            continue
        document, _ = read_glb(glb)
        for image in document.get("images", []):
            png = (glb.parent / image["uri"]).resolve()
            textures.add(png)
            if not png.is_file() or not inside(exports_root, png):
                bad_textures.append(f"{glb.as_posix()} -> {image['uri']}")
    partials = [path.as_posix() for path in output.rglob("*.partial")]
    return {"objs": len(objs), "glb_missing": missing, "partials": partials,
            "textures_missing": bad_textures, "textures_referenced": len(textures)}


def export_gltf(output, source=None, workers=0, only=None, limit=0, root=ROOT):
    source = Path(source) if source else root / "exports/bulk"
    models_root, exports_root = source / "models", Path(root) / "exports"
    output = prepare_output(output, root)
    for path in output.rglob("*.partial"):
        path.unlink()
    objs = list_objs(models_root, only)
    if limit:
        objs = objs[:limit]
    filter_modes = load_filter_modes(source, exports_root)
    journal = Journal(output / "journal.sqlite")
    previous = journal.previous()
    tasks = []
    for obj in objs:
        key = obj.relative_to(models_root).as_posix()
        glb = destination(models_root, output, obj)
        tasks.append((obj.as_posix(), glb.as_posix(), previous.get(key)))
    counts = {"ok": 0, "skipped": 0, "failed": 0}
    started = datetime.now(timezone.utc)
    workers = workers or os.cpu_count() or 1
    try:
        with ProcessPoolExecutor(max_workers=workers, initializer=init_worker,
                                 initargs=(exports_root, filter_modes)) as pool:
            for done, result in enumerate(pool.map(work_item, tasks, chunksize=8), 1):
                key = Path(result["obj"]).relative_to(models_root).as_posix()
                journal.put(key, Path(result["glb"]).relative_to(output).as_posix(), result)
                counts[result["status"]] += 1
                if result["status"] == "failed":
                    print(f"FALLO {key}: {result['error']}", file=sys.stderr)
                if done % 200 == 0:
                    journal.commit()
                    print(f"{done}/{len(tasks)} {counts}", file=sys.stderr, flush=True)
    finally:
        journal.commit()
        journal.close()
    check = verify(output, models_root, exports_root, objs)
    summary = {"schema_version": 1, "converter_revision": CONVERTER_REVISION, "objs": len(objs),
               **counts, "started_at_utc": started.isoformat(),
               "finished_at_utc": datetime.now(timezone.utc).isoformat(), "verify": check}
    if not only and not limit:
        (output / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps({key: value for key, value in summary.items() if key != "verify"}), file=sys.stderr)
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "exports/gltf")
    parser.add_argument("--source", type=Path, default=ROOT / "exports/bulk")
    parser.add_argument("--workers", type=int, default=0, help="Procesos en paralelo; 0 usa todos los núcleos")
    parser.add_argument("--limit", type=int, default=0, help="Máximo de OBJ; 0 convierte todos")
    parser.add_argument("--only", nargs="*", help="Solo estos OBJ (ruta completa o relativa a models/)")
    args = parser.parse_args()
    summary = export_gltf(args.output, args.source, args.workers, args.only, args.limit)
    check = summary["verify"]
    if summary["failed"] or check["glb_missing"] or check["partials"] or check["textures_missing"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
