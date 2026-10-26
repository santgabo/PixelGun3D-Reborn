"""Copia las armas de jugador a exports/weapons con nombre, categoría y textura local.

No vuelve a leer el APK. Usa el inventario, los prefabs weapons/weaponN,
la localización I2 y los GLB ya convertidos. Los props de mapa (Knife_statue
y similares), los brazos del jugador, las armas de enemigos y las de mech
no entran. Cada GLB lleva en su nodo la pose de reposo del prefab (hueso ×
bindpose), así todas las armas salen orientadas igual: cañón +Z, arriba +Y.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sqlite3
import struct
import unicodedata
from collections import defaultdict
from pathlib import Path

import UnityPy

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "pixelgun3d.weapons.v1"
WEAPON_SOUNDS_PATH = 295
WEAPON_RE = re.compile(r"weapons/weapon(\d+)$")
INNER_RE = re.compile(r"weaponsystem/inner/weapon(\d+)_inner$")
CATEGORIES = {
    1: ("primary", "Principal"),
    2: ("backup", "Reserva"),
    3: ("melee", "Cuerpo a cuerpo"),
    4: ("special", "Especial"),
    5: ("sniper", "Francotirador"),
    6: ("premium", "Premium"),
}
RARITY = {
    0: "Common", 1: "Uncommon", 2: "Rare", 3: "Epic", 4: "Legendary", 5: "Mythic",
}
LOW_TYPE = {
    0: "AssaultRifle_1", 1: "AssaultRifle_2", 2: "Shotgun_1", 3: "Shotgun_2",
    4: "Machinegun", 5: "Pistol_1", 6: "Pistol_2", 7: "Submachinegun",
    8: "Knife", 9: "Sword", 10: "Flamethrower_1", 11: "Flamethrower_2",
    12: "SniperRifle_1", 13: "SniperRifle_2", 14: "Bow",
    15: "RocketLauncher_1", 16: "RocketLauncher_2", 17: "RocketLauncher_3",
    18: "GrenadeLauncher", 19: "Snaryad", 20: "Snaryad_Otskok", 21: "Snaryad_Disk",
    22: "Railgun", 23: "Ray", 24: "AOE", 25: "Instant_Area_Damage",
    26: "X3_Snaryad", 27: "NOT_CHANGE",
}
FIELDS = [
    ("rarity", "i4"), ("typeForLow", "i4"), ("InShopEffects", "arr_i4"),
    ("zoomShop", "i4"), ("isSlowdown", "bool"), ("slowdownCoeff", "f4"), ("slowdownTime", "f4"),
    ("noFillObjects", "arr_pptr"), ("typeTracer", "i4"), ("typeDead", "i4"),
    ("gunFlash", "pptr"), ("gunFlashDouble", "arr_pptr"), ("lengthForShot", "f4"),
    ("damageByTier", "arr_f4"), ("dpses", "arr_f4"),
    ("tier", "i4"), ("categoryNabor", "i4"),
    ("isMechWeapon", "bool"), ("isGrenadeWeapon", "bool"),
    ("grenadeUseTime", "f4"), ("grenadeThrowTime", "f4"), ("fireRateShop", "i4"),
    ("filterMap", "arr_i4"), ("alternativeName", "str"),
    ("isBurstShooting", "bool"), ("countShootInBurst", "i4"), ("delayInBurstShooting", "f4"),
    ("isDaterWeapon", "bool"), ("daterMessage", "str"),
    ("ammoInClip", "i4"), ("InitialAmmo", "i4"), ("maxAmmo", "i4"), ("ammoForBonusShotMelee", "i4"),
    ("isMelee", "bool"), ("isRoundMelee", "bool"), ("isFrostSword", "bool"),
    ("frostRadius", "f4"), ("frostDamageMultiplier", "f4"), ("radiusRoundMelee", "f4"),
    ("isLoopShoot", "bool"), ("isCharging", "bool"), ("chargeLoop", "bool"),
    ("chargeMax", "i4"), ("chargeTime", "f4"), ("invisWhenCharged", "bool"),
    ("criticalHitChance", "i4"), ("criticalHitCoef", "f4"),
    ("isDamageHeal", "bool"), ("damageHealMultiplier", "f4"),
    ("isPoisoning", "bool"), ("poisonDamageMultiplier", "f4"),
    ("poisonCount", "i4"), ("poisonTime", "f4"), ("poisonType", "i4"),
    ("isShotGun", "bool"), ("isDoubleShot", "bool"), ("countShots", "i4"), ("isShotMelee", "bool"),
    ("isZooming", "bool"), ("fieldOfViewZomm", "f4"), ("isMagic", "bool"),
    ("flamethrower", "bool"), ("shocker", "bool"), ("snowStorm", "bool"), ("bulletExplode", "bool"),
    ("bazooka", "bool"), ("countInSeriaBazooka", "i4"), ("stepTimeInSeriaBazooka", "f4"),
    ("railgun", "bool"), ("railName", "str"), ("freezer", "bool"), ("countReflectionRay", "i4"),
    ("grenadeLauncher", "bool"), ("bazookaExplosionName", "str"),
    ("bazookaExplosionRadius", "f4"), ("bazookaExplosionRadiusSelf", "f4"),
    ("bazookaImpulseRadius", "f4"), ("impulseForce", "f4"), ("impulseForceSelf", "f4"),
    ("range", "f4"), ("shockerRange", "f4"), ("shockerDamageMultiplier", "f4"),
    ("snowStormBonusRange", "f4"), ("snowStormBonusMultiplier", "f4"),
    ("damage", "i4"), ("speedModifier", "f4"), ("Probability", "i4"),
    ("damageRange", "vec2"), ("gunPosition", "vec3"), ("inAppExtensionModifier", "i4"),
    ("meleeAngle", "f4"), ("multiplayerDamage", "f4"), ("meleeAttackTimeModifier", "f4"),
    ("startZone", "vec2"),
    ("tekKoof", "f4"), ("upKoofFire", "f4"), ("maxKoof", "f4"), ("downKoofFirst", "f4"), ("downKoof", "f4"),
    ("campaignOnly", "bool"), ("rocketNum", "i4"), ("scopeNum", "i4"), ("scaleShop", "f4"),
    ("positionShop", "vec3"), ("rotationShop", "vec3"),
    ("specialEffect", "i4"), ("protectionEffectValue", "f4"),
    ("localizeWeaponKey", "str"),
]
ICON_RE = re.compile(r"^(?P<stem>.+?)_?[Ii]con(?P<level>\d+)_[Bb]ig$")
ARM_RE = re.compile(r"^(arms?(mesh)?|player\d+)$")
EFFECT_WORDS = ("particle", "muzzle", "tracer")


def align(pos, n=4):
    return (pos + n - 1) & ~(n - 1)


def slugify(text):
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return text or "weapon"


def norm_keys(text):
    base = re.sub(r"[^a-z0-9]", "", text.lower())
    keys = {base} if base else set()
    if "pixl" in base:
        keys.add(base.replace("pixl", "pixel"))
    if "pixel" in base:
        keys.add(base.replace("pixel", "pixl"))
    if base.endswith("buy"):
        keys.add(base[:-3])
    return {key for key in keys if key}

def stem_keys(stem):
    keys = list(norm_keys(stem))
    stripped = re.sub(r"[\s_-]*\d+$", "", stem)
    if stripped and stripped != stem:
        for key in norm_keys(stripped):
            if key not in keys:
                keys.append(key)
    return keys



def mesh_stem(name):
    return re.sub(r"(?i)([_\s-]*mesh)([_\s-]*\d+)?$", "", name).strip(" _-")


def is_arm(name):
    compact = re.sub(r"[^a-z0-9]", "", name.lower())
    if "fpsplayer" in compact or compact.startswith("arms"):
        return True
    return bool(ARM_RE.fullmatch(compact))


def is_effect(name):
    low = name.lower()
    return any(word in low for word in EFFECT_WORDS)


def audio_role(name):
    low = name.lower()
    # El orden importa: "PlasmaShotgun_Empty" o "firestorm_zoom_in" contienen
    # "shot"/"fire" pero no son disparos.
    if "reload" in low or "reoad" in low:
        return "reload"
    if "zoom" in low or "scope" in low:
        return "scope"
    if "empty" in low or "click" in low:
        return "empty"
    if any(word in low for word in ("shoot", "shot", "fire")):
        return "shoot"
    return "other"


def mat_mul(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def identity():
    return [[float(i == j) for j in range(4)] for i in range(4)]


def local_matrix(transform):
    """Matriz local (fila mayor) de un Transform de Unity: T * R * S."""
    q, p, s = transform.m_LocalRotation, transform.m_LocalPosition, transform.m_LocalScale
    x, y, z, w = q.x, q.y, q.z, q.w
    rotation = [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ]
    scale, position = (s.x, s.y, s.z), (p.x, p.y, p.z)
    return [
        [rotation[i][j] * scale[j] for j in range(3)] + [position[i]] for i in range(3)
    ] + [[0.0, 0.0, 0.0, 1.0]]


def unity_matrix(value):
    return [[float(getattr(value, f"e{row}{col}")) for col in range(4)] for row in range(4)]


def gltf_matrix(matrix):
    """Pasa una matriz de Unity al espacio del GLB (X reflejada), en orden de columnas."""
    mirror = (-1.0, 1.0, 1.0, 1.0)
    return [round(mirror[row] * matrix[row][col] * mirror[col], 6) + 0.0 for col in range(4) for row in range(4)]


def rest_matrix(transform_id, transforms):
    """Transformación del objeto respecto a la raíz del prefab (la raíz no cuenta)."""
    matrix = identity()
    while transform_id in transforms:
        transform = transforms[transform_id]
        father = getattr(transform, "m_Father", None)
        father_id = getattr(father, "path_id", 0) if father is not None else 0
        if not father_id:
            break
        matrix = mat_mul(local_matrix(transform), matrix)
        transform_id = father_id
    return matrix


def cached_env(file_id, files, cache, root):
    env = cache.get(file_id)
    if env is None:
        archive, logical = files[file_id]
        env = UnityPy.load(str(root / "work/prepared" / archive / logical))
        cache[file_id] = env
    return env


def bind_poses(mesh, owner_file, externals, files, cache, root):
    target = owner_file if mesh.file_id == 0 else externals.get((owner_file, mesh.file_id))
    if target is None:
        return []
    menv = cached_env(target, files, cache, root)
    data = next((obj.read() for obj in menv.objects if obj.path_id == mesh.path_id and obj.type.name == "Mesh"), None)
    return [unity_matrix(item) for item in getattr(data, "m_BindPose", None) or []]


def part_matrix(kind, data, go_id, mesh, transforms, transform_of_go, owner_file, externals, files, cache, root):
    """Pose de reposo de la malla en el prefab, en el espacio del GLB.

    Una malla con piel se coloca con hueso * bindpose; el Transform de su
    GameObject no interviene. Sin piel, manda el Transform del GameObject.
    """
    if kind == "SkinnedMeshRenderer":
        poses = bind_poses(mesh, owner_file, externals, files, cache, root)
        for index, bone in enumerate(getattr(data, "m_Bones", None) or []):
            if index < len(poses) and bone.file_id == 0 and bone.path_id in transforms:
                return gltf_matrix(mat_mul(rest_matrix(bone.path_id, transforms), poses[index]))
    transform_id = transform_of_go.get(go_id)
    return None if transform_id is None else gltf_matrix(rest_matrix(transform_id, transforms))


def role_of(name):
    if is_arm(name):
        return "arm"
    if is_effect(name):
        return "effect"
    return "weapon"


def parse_weapon_sounds(raw, start=32):
    pos = start

    def need(n):
        nonlocal pos
        if pos + n > len(raw):
            raise EOFError(f"faltan {n} bytes en {pos}/{len(raw)}")
        chunk = raw[pos:pos + n]
        pos += n
        return chunk

    out = {}
    for name, typ in FIELDS:
        pos = align(pos, 4)
        if typ == "i4":
            out[name] = struct.unpack_from("<i", need(4))[0]
        elif typ == "f4":
            out[name] = struct.unpack_from("<f", need(4))[0]
        elif typ == "bool":
            out[name] = bool(need(1)[0])
            pos = align(pos, 4)
        elif typ == "str":
            n = struct.unpack_from("<i", need(4))[0]
            if n < 0 or n > 400:
                raise ValueError(f"{name} longitud {n}")
            out[name] = need(n).split(b"\0")[0].decode("utf-8", "replace")
            pos = align(pos, 4)
        elif typ == "pptr":
            out[name] = struct.unpack_from("<iq", need(12))
        elif typ == "vec2":
            out[name] = struct.unpack_from("<ff", need(8))
        elif typ == "vec3":
            out[name] = struct.unpack_from("<fff", need(12))
        elif typ in ("arr_i4", "arr_f4"):
            n = struct.unpack_from("<i", need(4))[0]
            if n < 0 or n > 200:
                raise ValueError(f"{name} cantidad {n}")
            fmt = "<" + ("i" if typ == "arr_i4" else "f") * n
            out[name] = list(struct.unpack_from(fmt, need(4 * n))) if n else []
        elif typ == "arr_pptr":
            n = struct.unpack_from("<i", need(4))[0]
            if n < 0 or n > 200:
                raise ValueError(f"{name} cantidad {n}")
            out[name] = [struct.unpack_from("<iq", need(12)) for _ in range(n)]
        else:
            raise ValueError(typ)
    return out


def weapon_sounds_blob(env):
    found = []
    for obj in env.objects:
        if obj.type.name != "MonoBehaviour":
            continue
        raw = obj.get_raw_data()
        if len(raw) < 32:
            continue
        file_id, path_id = struct.unpack_from("<iq", raw, 16)
        if path_id == WEAPON_SOUNDS_PATH:
            found.append((file_id, raw))
    if not found:
        return None
    for file_id, raw in found:
        if file_id == 1:
            return raw
    return found[0][1]


def english_names(raw):
    names = {}
    idx = 0
    while True:
        i = raw.find(b"Key_", idx)
        if i < 0:
            break
        idx = i + 4
        if i < 4:
            continue
        n = struct.unpack_from("<i", raw, i - 4)[0]
        if not 0 < n < 40 or i + n > len(raw) or not raw[i:i + n].startswith(b"Key_"):
            continue
        key = raw[i:i + n].split(b"\0")[0].decode()
        pos = align(i + n, 4)
        if pos + 8 > len(raw):
            continue
        pos += 4
        dlen = struct.unpack_from("<i", raw, pos)[0]
        if dlen < 0 or dlen > 2000 or pos + 4 + dlen > len(raw):
            continue
        pos = align(pos + 4 + dlen, 4)
        if pos + 8 > len(raw):
            continue
        count = struct.unpack_from("<i", raw, pos)[0]
        pos += 4
        if not 1 <= count <= 30 or pos + 4 > len(raw):
            continue
        elen = struct.unpack_from("<i", raw, pos)[0]
        if elen < 0 or elen > 500 or pos + 4 + elen > len(raw):
            continue
        english = raw[pos + 4:pos + 4 + elen].split(b"\0")[0].decode("utf-8", "replace").strip()
        names.setdefault(key, english)
    return names


def choose_primary(parts):
    weapon_parts = [part for part in parts if part["role"] == "weapon"]
    viewmodel = False
    if weapon_parts:
        pool = [part for part in weapon_parts if part.get("source_glb")] or weapon_parts
    else:
        pool = [part for part in parts if part["role"] == "arm" and part.get("source_glb")]
        viewmodel = bool(pool)
    if not pool:
        return None
    ranked = [part for part in pool if part["vertices"] > 0] or pool
    chosen = max(ranked, key=lambda part: (
        part["vertices"],
        "mesh" in part["object_name"].lower(),
        part["object_name"],
    ))
    if viewmodel:
        chosen["role"] = "viewmodel"
    return chosen


def disambiguate(weapons):
    groups = defaultdict(list)
    for weapon in weapons:
        groups[weapon["name"]].append(weapon)
    for name, group in groups.items():
        if len(group) < 2:
            continue
        stems = []
        for weapon in group:
            primary = weapon.get("primary") or {}
            stems.append(mesh_stem(primary.get("object_name") or "") or primary.get("mesh_name") or "")
        stem_unique = len(set(stems)) == len(group) and all(stems)
        tier_unique = len({weapon["tier"] for weapon in group}) == len(group)
        for weapon, stem in zip(group, stems):
            if stem_unique and stem.lower() != name.lower():
                extra = stem
            elif tier_unique:
                extra = f"tier {weapon['tier']}"
            else:
                extra = weapon["id"]
            weapon["name"] = f"{name} ({extra})"
            weapon["aliases"] = sorted(set(weapon.get("aliases") or []) | {weapon["name"], extra, weapon["id"]})


def output_path(payload, suffix):
    for item in json.loads(payload or "[]"):
        if item["path"].endswith(suffix):
            return item["path"]
    return None


def split_glb(data):
    if data[:4] != b"glTF":
        raise ValueError("no es GLB")
    length = struct.unpack_from("<I", data, 8)[0]
    if length != len(data):
        raise ValueError(f"longitud GLB {length} != {len(data)}")
    off = 12
    chunks = []
    while off + 8 <= length:
        chunk_len, chunk_type = struct.unpack_from("<I4s", data, off)
        chunks.append((chunk_type, data[off + 8:off + 8 + chunk_len]))
        off += 8 + chunk_len
    if not chunks or chunks[0][0] != b"JSON":
        raise ValueError("GLB sin chunk JSON")
    return chunks


def write_glb(path, document, binary):
    payload = json.dumps(document, separators=(",", ":")).encode()
    payload += b" " * (-len(payload) % 4)
    if binary:
        binary += b"\0" * (-len(binary) % 4)
    total = 12 + 8 + len(payload) + (8 + len(binary) if binary else 0)
    out = bytearray(struct.pack("<III", 0x46546C67, 2, total))
    out += struct.pack("<I4s", len(payload), b"JSON")
    out += payload
    if binary:
        out += struct.pack("<I4s", len(binary), b"BIN\0")
        out += binary
    path.write_bytes(out)


def localize_textures(src_glb, dst_glb, label, extras=None, matrix=None):
    chunks = split_glb(src_glb.read_bytes())
    document = json.loads(chunks[0][1])
    binary = next((blob for kind, blob in chunks if kind == b"BIN\0"), b"")
    copied = []
    images = document.get("images") or []
    stem = dst_glb.stem
    for index, image in enumerate(images):
        uri = image.get("uri")
        if not uri or uri.startswith("data:"):
            continue
        source = (src_glb.parent / uri).resolve()
        if not source.is_file():
            raise FileNotFoundError(source)
        filename = f"{stem}.png" if index == 0 else f"{stem}-{index + 1}.png"
        shutil.copyfile(source, dst_glb.parent / filename)
        image["uri"] = filename
        copied.append({"file": filename, "source_name": source.name})
    if document.get("nodes"):
        document["nodes"][0]["name"] = label
        if matrix is not None:
            for key in ("translation", "rotation", "scale"):
                document["nodes"][0].pop(key, None)
            document["nodes"][0]["matrix"] = matrix
    if document.get("meshes"):
        document["meshes"][0]["name"] = label
    if extras:
        document.setdefault("asset", {}).setdefault("extras", {}).update(extras)
    write_glb(dst_glb, document, binary)
    return copied


def main_texture(data, owner_file, env, externals, files, cache, root):
    mats = getattr(data, "m_Materials", None) or []
    if not mats or mats[0] is None or not getattr(mats[0], "path_id", 0):
        return None
    mat = mats[0]
    if mat.file_id == 0:
        mat_file, menv = owner_file, env
    else:
        mat_file = externals.get((owner_file, mat.file_id))
        if not mat_file:
            return None
        menv = cached_env(mat_file, files, cache, root)
    material = next((
        obj.read() for obj in menv.objects
        if obj.path_id == mat.path_id and obj.type.name == "Material"
    ), None)
    if material is None:
        return None
    for prop, texenv in material.m_SavedProperties.m_TexEnvs:
        if getattr(prop, "name", None) != "_MainTex":
            continue
        tex = texenv.m_Texture
        if tex is None or not getattr(tex, "path_id", 0):
            return None
        if tex.file_id == 0:
            return (mat_file, tex.path_id)
        target = externals.get((mat_file, tex.file_id))
        return None if target is None else (target, tex.path_id)
    return None


def pick_variant(detail, file_id, path_id):
    variants = (detail or {}).get("variants") or []
    for variant in variants:
        renderer = variant.get("renderer") or {}
        if renderer.get("file_id") == file_id and renderer.get("path_id") == path_id:
            return variant, "renderer"
    for variant in variants:
        if variant.get("preferred"):
            return variant, "preferred_fallback"
    if variants:
        return variants[0], "first_fallback"
    return None, "missing"


def icon_for(weapon, icons):
    stems = [mesh_stem(part["object_name"]) for part in weapon["parts"] if part["role"] != "arm"]
    stems.extend([weapon["name"], weapon["tag"]])
    seen = set()
    for stem in stems:
        if not stem:
            continue
        for key in stem_keys(stem):
            if key in seen:
                continue
            seen.add(key)
            families = icons.get(key)
            if not families:
                continue
            values = list(families.values())
            if len(values) == 1:
                return values[0], "alias"
            exact = [family for family in values if set(stem_keys(family["stem"])) & set(stem_keys(stem))]
            if len(exact) == 1:
                return exact[0], "exact"
    return None, "none"


def pick_icon_level(family, tier):
    levels = family["levels"]
    wanted = tier + 1
    if wanted in levels:
        return levels[wanted], wanted
    level = min(levels)
    return levels[level], level


def assign_slugs(weapons):
    groups = defaultdict(list)
    for weapon in weapons:
        groups[slugify(weapon["name"])].append(weapon)
    used = set()
    for base, group in groups.items():
        for weapon in group:
            slug = base if len(group) == 1 else f"{base}-w{weapon['number']}"
            candidate, n = slug, 2
            while candidate in used:
                candidate = f"{slug}-{n}"
                n += 1
            weapon["slug"] = candidate
            used.add(candidate)


def read_parts(path, owner_file, externals, mesh_journal, glb_of, root, files, cache):
    env = UnityPy.load(str(path))
    names = {}
    filters = {}
    renderers = []
    transforms = {}
    transform_of_go = {}
    for obj in env.objects:
        if obj.type.name == "GameObject":
            names[obj.path_id] = obj.read().m_Name or ""
        elif obj.type.name == "Transform":
            transform = obj.read()
            transforms[obj.path_id] = transform
            go = getattr(transform, "m_GameObject", None)
            if go is not None:
                transform_of_go[go.path_id] = obj.path_id
        elif obj.type.name == "MeshFilter":
            try:
                data = obj.read()
            except Exception:
                continue
            go = getattr(data, "m_GameObject", None)
            mesh = getattr(data, "m_Mesh", None)
            if go is not None and mesh is not None and getattr(mesh, "path_id", 0):
                filters[go.path_id] = mesh
        elif obj.type.name in ("SkinnedMeshRenderer", "MeshRenderer", "ParticleSystemRenderer"):
            renderers.append(obj)

    def append(mesh, go_id, renderer_path_id, forced_role=None, main_tex=None, matrix=None):
        target = owner_file if mesh.file_id == 0 else externals.get((owner_file, mesh.file_id))
        if target is None:
            return
        key = (target, mesh.path_id, renderer_path_id)
        if key in seen:
            return
        seen.add(key)
        go_name = names.get(go_id, "") or ""
        journal = mesh_journal.get((target, mesh.path_id))
        mesh_name = journal[0] if journal else go_name
        detail = json.loads(journal[2]) if journal and journal[2] else {}
        variant, match = pick_variant(detail, owner_file, renderer_path_id)
        obj_rel = variant.get("obj") if variant else None
        glb_rel = glb_of.get(obj_rel[len("models/"):]) if obj_rel and obj_rel.startswith("models/") else None
        material = variant["materials"][0].get("name") if variant and variant.get("materials") else None
        parts.append({
            "object_name": go_name or mesh_name,
            "mesh_name": mesh_name,
            "role": forced_role or role_of(go_name or mesh_name),
            "vertices": detail.get("vertices") or 0,
            "texture_match": match,
            "material": material,
            "main_tex": main_tex,
            "source_glb": None if glb_rel is None else str(root / "exports/gltf" / glb_rel),
            "renderer_path_id": renderer_path_id,
            "matrix": matrix,
        })

    parts = []
    seen = set()
    used_gos = set()
    for obj in renderers:
        try:
            data = obj.read()
        except Exception:
            continue
        go = getattr(data, "m_GameObject", None)
        go_id = go.path_id if go is not None else 0
        mesh = getattr(data, "m_Mesh", None)
        if mesh is None or not getattr(mesh, "path_id", 0):
            mesh = filters.get(go_id)
        if mesh is None or not getattr(mesh, "path_id", 0):
            continue
        used_gos.add(go_id)
        role = "effect" if obj.type.name == "ParticleSystemRenderer" else None
        tex = None
        if obj.type.name != "ParticleSystemRenderer":
            try:
                tex = main_texture(data, owner_file, env, externals, files, cache, root)
            except Exception:
                tex = None
        matrix = part_matrix(
            obj.type.name, data, go_id, mesh, transforms, transform_of_go,
            owner_file, externals, files, cache, root,
        )
        append(mesh, go_id, obj.path_id, role, tex, matrix)
    for go_id, mesh in filters.items():
        if go_id not in used_gos:
            matrix = part_matrix(
                "MeshFilter", None, go_id, mesh, transforms, transform_of_go,
                owner_file, externals, files, cache, root,
            )
            append(mesh, go_id, 0, matrix=matrix)
    return parts


def prepare_output(output):
    if output.exists() and any(output.iterdir()):
        marker = output / "catalog.json"
        previous = json.loads(marker.read_text()) if marker.is_file() else {}
        if previous.get("schema") != SCHEMA:
            raise SystemExit(f"{output} ya tiene archivos que no son esta extracción")
        # Vaciar sin borrar la carpeta: `npm run dev` la publica y dejaría de
        # servirla si se sustituye por otra.
        for child in output.iterdir():
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
    output.mkdir(parents=True, exist_ok=True)


def check_known(weapons):
    by_id = {weapon["id"]: weapon for weapon in weapons}
    expected = {
        "weapon1": ("Pixel Gun", "backup"),
        "weapon10": ("Combat Rifle", "primary"),
        "weapon116": ("Scythe", "melee"),
    }
    for wid, (name, category) in expected.items():
        weapon = by_id.get(wid)
        if weapon is None or weapon["name"] != name or weapon["category"] != category:
            raise SystemExit(f"comprobación fallida: {wid} -> {weapon}")
        if not weapon.get("primary") or not weapon["primary"].get("source_glb"):
            raise SystemExit(f"{wid} no tiene modelo")
    for category in ("sniper", "special", "premium"):
        if not any(weapon["category"] == category for weapon in weapons):
            raise SystemExit(f"ninguna arma salió como {category}")


def apply_main_tex(part, folder, texture_of, bulk):
    main = part.get("main_tex")
    textures = part.get("textures") or []
    if not main or not textures:
        return
    png = texture_of.get(main)
    if not png:
        return
    source = bulk / png
    dest = folder / textures[0]["file"]
    if not source.is_file() or not dest.is_file():
        return
    if dest.read_bytes() == source.read_bytes():
        return
    shutil.copyfile(source, dest)
    textures[0]["source_name"] = source.name
    part["texture_match"] = "main_tex"


def write_weapon_files(weapon, folder, output, bulk, texture_of):
    primary = weapon.get("primary")
    used = set()
    extras = {"id": weapon["id"], "name": weapon["name"], "category": weapon["category"]}
    if primary and primary.get("source_glb"):
        primary["file"] = f"{weapon['slug']}.glb"
        primary["textures"] = localize_textures(
            Path(primary["source_glb"]), folder / primary["file"], weapon["name"], extras, primary.get("matrix"),
        )
        apply_main_tex(primary, folder, texture_of, bulk)
        used.add(primary["file"])
    for index, part in enumerate(weapon["parts"], start=1):
        if part is primary or part["role"] == "arm" or not part.get("source_glb"):
            continue
        part_slug = slugify(part["object_name"]) or f"part-{index}"
        filename = f"{weapon['slug']}--{part_slug}.glb"
        n = 2
        while filename in used:
            filename = f"{weapon['slug']}--{part_slug}-{n}.glb"
            n += 1
        used.add(filename)
        part["file"] = filename
        part["textures"] = localize_textures(
            Path(part["source_glb"]), folder / filename, part["object_name"], extras, part.get("matrix"),
        )
        apply_main_tex(part, folder, texture_of, bulk)
    icon = weapon.get("icon_src")
    if icon:
        dest = folder / f"{weapon['slug']}-icon.png"
        shutil.copyfile(bulk / icon["path"], dest)
        weapon["icon_rel"] = dest.relative_to(output).as_posix()
        weapon["icon_name"] = icon["name"]
    else:
        weapon["icon_rel"] = None
        weapon["icon_name"] = None
    audio_out = []
    role_count = defaultdict(int)
    for clip in weapon.get("audio_src") or []:
        if not clip.get("source"):
            continue
        role_count[clip["role"]] += 1
        suffix = "" if role_count[clip["role"]] == 1 else f"-{role_count[clip['role']]}"
        filename = f"{weapon['slug']}-{clip['role']}{suffix}.wav"
        shutil.copyfile(bulk / clip["source"], folder / filename)
        audio_out.append({
            "name": clip["name"],
            "role": clip["role"],
            "file": (folder / filename).relative_to(output).as_posix(),
        })
    weapon["audio_out"] = audio_out


def build_record(weapon, folder, output):
    primary = weapon.get("primary") if weapon.get("primary") and weapon["primary"].get("file") else None
    model = None if primary is None else (folder / primary["file"]).relative_to(output).as_posix()
    textures = [] if primary is None else [
        (folder / item["file"]).relative_to(output).as_posix() for item in primary.get("textures") or []
    ]
    parts = []
    for part in weapon["parts"]:
        if part is weapon.get("primary") or part["role"] == "arm" or not part.get("file"):
            continue
        parts.append({
            "name": part["object_name"],
            "role": part["role"],
            "file": (folder / part["file"]).relative_to(output).as_posix(),
            "vertices": part["vertices"],
            "texture_match": part["texture_match"],
            "material": part.get("material"),
            "source_mesh": part["mesh_name"],
        })
    return {
        "id": weapon["id"],
        "number": weapon["number"],
        "name": weapon["name"],
        "slug": weapon["slug"],
        "category": weapon["category"],
        "category_label": weapon["category_label"],
        "category_id": weapon["category_id"],
        "kind": slugify(weapon["low_type"]),
        "low_type": weapon["low_type"],
        "tier": weapon["tier"],
        "rarity": weapon["rarity"],
        "tag": weapon["tag"],
        "localization_key": weapon["key"],
        "aliases": weapon["aliases"],
        "folder": folder.relative_to(output).as_posix(),
        "model": model,
        "model_role": None if primary is None else primary.get("role"),
        # El GLB lleva en su nodo la pose del prefab: cañón hacia +Z, arriba +Y.
        "rest_pose": primary is not None and primary.get("matrix") is not None,
        "textures": textures,
        "texture_match": None if primary is None else primary.get("texture_match"),
        "icon": weapon.get("icon_rel"),
        "icon_name": weapon.get("icon_name"),
        "parts": parts,
        "audio": weapon.get("audio_out") or [],
        "stats": {
            "damage": weapon["damage"],
            "ammo_in_clip": weapon["ammo"],
            "max_ammo": weapon["max_ammo"],
            "fire_rate_shop": weapon["fire_rate"],
            "range": round(weapon["range"], 4),
            "zoom": weapon["zoom"],
            "melee": weapon["melee"],
            "shotgun": weapon["shotgun"],
            "bazooka": weapon["bazooka"],
            "railgun": weapon["railgun"],
            "flamethrower": weapon["flamethrower"],
            "campaign_only": weapon["campaign_only"],
        },
        "source": {
            "prefab": weapon["prefab"],
            "inner": weapon.get("inner"),
            "source_glb": None if primary is None else primary.get("source_glb"),
        },
        "status": "ok" if model else weapon["status"] if weapon["status"] != "ok" else "no_model",
    }


def alias_index(records):
    buckets = defaultdict(set)
    for item in records:
        keys = set(item["aliases"]) | {item["slug"], item["id"]}
        for alias in keys:
            buckets[alias.lower()].add(item["id"])
    unique = {alias: next(iter(ids)) for alias, ids in buckets.items() if len(ids) == 1}
    ambiguous = {alias: sorted(ids) for alias, ids in buckets.items() if len(ids) > 1}
    return unique, ambiguous


def dict_counts(records):
    counts, status = defaultdict(int), defaultdict(int)
    icons = sum(item["icon"] is not None for item in records)
    exact = sum(item.get("texture_match") == "renderer" for item in records)
    posed = sum(bool(item.get("rest_pose")) for item in records)
    for item in records:
        counts[item["category"]] += 1
        status[item["status"]] += 1
    return {
        "by_category": dict(sorted(counts.items())),
        "by_status": dict(sorted(status.items())),
        "with_icon": icons,
        "texture_match_renderer": exact,
        "with_rest_pose": posed,
    }


def verify(output, records):
    missing = []
    for item in records:
        if not item["model"]:
            continue
        model = output / item["model"]
        if not model.is_file() or model.read_bytes()[:4] != b"glTF":
            missing.append(item["id"])
            continue
        document = json.loads(split_glb(model.read_bytes())[0][1])
        for image in document.get("images") or []:
            uri = image.get("uri")
            if uri and not uri.startswith("data:") and not (model.parent / uri).is_file():
                missing.append(f"{item['id']}:{uri}")
    if missing:
        raise SystemExit(f"GLB o textura ausente: {missing[:8]}")


def extract(root=ROOT, output=None):
    root = Path(root)
    output = Path(output) if output else root / "exports/weapons"
    inventory = sqlite3.connect(f"file:{root / 'work/inventory/resources.sqlite'}?mode=ro", uri=True)
    bulk = sqlite3.connect(f"file:{root / 'exports/bulk/journal.sqlite'}?mode=ro", uri=True)
    gltf = sqlite3.connect(f"file:{root / 'exports/gltf/journal.sqlite'}?mode=ro", uri=True)
    prepared = root / "work/prepared"
    bulk_root = root / "exports/bulk"

    weapons_rows = []
    for logical, file_id, archive, logical_path in inventory.execute("""
        SELECT l.logical_name, l.target_file, f.archive, f.logical_path
        FROM links l JOIN files f ON f.id = l.target_file
        WHERE l.logical_name LIKE 'weapons/weapon%'
    """):
        match = WEAPON_RE.fullmatch(logical)
        if match:
            weapons_rows.append((int(match.group(1)), file_id, archive, logical_path))
    weapons_rows.sort()
    inners = {}
    for logical, file_id, logical_path in inventory.execute("""
        SELECT l.logical_name, l.target_file, f.logical_path
        FROM links l JOIN files f ON f.id = l.target_file
        WHERE l.logical_name LIKE 'weaponsystem/inner/weapon%'
    """):
        match = INNER_RE.fullmatch(logical)
        if match:
            inners[int(match.group(1))] = (file_id, logical_path)
    files = {
        fid: (archive, path)
        for fid, archive, path in inventory.execute("SELECT id, archive, logical_path FROM files")
    }
    externals = {
        (owner, ext): target
        for owner, ext, target in inventory.execute(
            "SELECT owner_file, external_id, target_file FROM externals WHERE target_file IS NOT NULL"
        )
    }
    mesh_journal = {
        (file_id, path_id): (name, output_json, detail_json)
        for file_id, path_id, name, output_json, detail_json in bulk.execute(
            "SELECT file_id, path_id, name, output_json, detail_json FROM items WHERE kind='mesh' AND status='ok'"
        )
    }
    glb_of = {
        obj: glb
        for obj, glb, status in gltf.execute("SELECT obj_path, glb_path, status FROM models")
        if status == "ok"
    }
    audio_of = {}
    for file_id, path_id, name, output_json in bulk.execute(
        "SELECT file_id, path_id, name, output_json FROM items WHERE kind='audio' AND status='ok'"
    ):
        audio_of[(file_id, path_id)] = (name, output_path(output_json, ".wav"))
    clips_in_file = defaultdict(list)
    for file_id, path_id, name in inventory.execute(
        "SELECT file_id, path_id, name FROM objects WHERE type='AudioClip'"
    ):
        clips_in_file[file_id].append((path_id, name))
    audio_by_owner = defaultdict(list)
    seen_clip = set()
    for (owner, _ext), target in externals.items():
        clips = clips_in_file.get(target) or []
        if not clips or len(clips) > 8:
            continue
        for path_id, name in clips:
            item = audio_of.get((target, path_id))
            if not item or (owner, target, path_id) in seen_clip:
                continue
            seen_clip.add((owner, target, path_id))
            wav_name, wav_path = item
            audio_by_owner[owner].append({
                "name": wav_name or name,
                "role": audio_role(wav_name or name or ""),
                "source": wav_path,
            })
    texture_of = {
        (file_id, path_id): output_path(output_json, ".png")
        for file_id, path_id, output_json in bulk.execute(
            "SELECT file_id, path_id, output_json FROM items WHERE kind='texture' AND status='ok'"
        )
    }
    icons = defaultdict(dict)
    for name, file_id, path_id in inventory.execute("""
        SELECT name, file_id, path_id FROM objects
        WHERE type='Texture2D' AND (name LIKE '%icon%big' OR name LIKE '%Icon%big')
    """):
        match = ICON_RE.match(name)
        png = texture_of.get((file_id, path_id))
        if not match or not png:
            continue
        stem, level = match.group("stem"), int(match.group("level"))
        for key in norm_keys(stem):
            icons[key].setdefault(stem, {"stem": stem, "levels": {}})
            icons[key][stem]["levels"][level] = {"name": name, "path": png}
    exact_icon_keys = set(icons)
    for families in list(icons.values()):
        for stem, family in list(families.items()):
            stripped = re.sub(r"[\s_-]*\d+$", "", stem)
            if not stripped or stripped == stem:
                continue
            for alias in norm_keys(stripped):
                if alias in exact_icon_keys:
                    continue
                icons[alias].setdefault(stem, family)

    loc_env = UnityPy.load(str(prepared / "obb/assets/bin/Data/bed523bdfde30aa46b86b162d19c6a82"))
    loc_raw = next(obj.get_raw_data() for obj in loc_env.objects if obj.type.name == "MonoBehaviour")
    english = english_names(loc_raw)
    print(f"localización {len(english)} claves, armas {len(weapons_rows)}", flush=True)

    env_cache = {}
    weapons = []
    failures = []
    for number, file_id, archive, logical_path in weapons_rows:
        prefab = prepared / archive / logical_path
        try:
            raw = weapon_sounds_blob(UnityPy.load(str(prefab)))
            if raw is None:
                raise ValueError("sin WeaponSounds")
            parsed = parse_weapon_sounds(raw)
        except Exception as error:
            failures.append({"id": f"weapon{number}", "stage": "prefab", "error": str(error)})
            continue
        category_id = parsed["categoryNabor"]
        category, label = CATEGORIES.get(category_id, ("uncategorized", "Sin categoría"))
        key = parsed["localizeWeaponKey"]
        low = LOW_TYPE.get(parsed["typeForLow"], f"type_{parsed['typeForLow']}")
        weapon = {
            "id": f"weapon{number}",
            "number": number,
            "name": english.get(key) or parsed["alternativeName"] or f"Weapon {number}",
            "category": category,
            "category_label": label,
            "category_id": category_id,
            "tier": parsed["tier"],
            "rarity": RARITY.get(parsed["rarity"], f"rarity_{parsed['rarity']}"),
            "tag": parsed["alternativeName"],
            "key": key,
            "low_type": low,
            "damage": parsed["damage"],
            "ammo": parsed["ammoInClip"],
            "max_ammo": parsed["maxAmmo"],
            "fire_rate": parsed["fireRateShop"],
            "range": parsed["range"],
            "zoom": parsed["isZooming"],
            "melee": parsed["isMelee"],
            "shotgun": parsed["isShotGun"],
            "bazooka": parsed["bazooka"],
            "railgun": parsed["railgun"],
            "flamethrower": parsed["flamethrower"],
            "campaign_only": parsed["campaignOnly"],
            "prefab": logical_path,
            "prefab_file": file_id,
            "parts": [],
            "status": "ok",
        }
        inner = inners.get(number)
        if inner:
            inner_id, inner_path = inner
            weapon["inner"] = inner_path
            weapon["inner_file"] = inner_id
            archive_inner = files[inner_id][0]
            try:
                weapon["parts"] = read_parts(
                    prepared / archive_inner / inner_path,
                    inner_id, externals, mesh_journal, glb_of, root, files, env_cache,
                )
            except Exception as error:
                weapon["status"] = "inner_failed"
                weapon["error"] = str(error)
        else:
            weapon["status"] = "no_inner"
        weapon["primary"] = choose_primary(weapon["parts"])
        if weapon["status"] == "ok" and (weapon["primary"] is None or not weapon["primary"].get("source_glb")):
            weapon["status"] = "no_model"
        family, how = icon_for(weapon, icons)
        weapon["icon_match"] = how
        if family:
            chosen, level = pick_icon_level(family, weapon["tier"])
            weapon["icon_src"] = chosen
            weapon["icon_level"] = level
        clips = []
        seen = set()
        for owner in (file_id, weapon.get("inner_file")):
            for clip in audio_by_owner.get(owner, []):
                marker = (clip["source"], clip["name"])
                if marker in seen:
                    continue
                seen.add(marker)
                clips.append(clip)
        weapon["audio_src"] = clips
        stems = []
        for part in weapon["parts"]:
            if part["role"] != "arm":
                stems.extend([part["object_name"], mesh_stem(part["object_name"]), part["mesh_name"]])
        weapon["aliases"] = sorted({item for item in [weapon["name"], weapon["tag"], weapon["id"], weapon["low_type"], *stems] if item})
        weapons.append(weapon)
        if len(weapons) % 40 == 0:
            print(f"clasificadas {len(weapons)}", flush=True)

    check_known(weapons)
    disambiguate(weapons)
    assign_slugs(weapons)
    prepare_output(output)
    records = []
    for index, weapon in enumerate(weapons, start=1):
        folder = output / weapon["category"] / weapon["slug"]
        folder.mkdir(parents=True, exist_ok=True)
        write_weapon_files(weapon, folder, output, bulk_root, texture_of)
        record = build_record(weapon, folder, output)
        (folder / "weapon.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
        records.append(record)
        if index % 40 == 0:
            print(f"copiadas {index}", flush=True)

    records.sort(key=lambda item: (item["category"], item["name"].lower(), item["number"]))
    unique_aliases, ambiguous_aliases = alias_index(records)
    catalog = {
        "schema": SCHEMA,
        "description": (
            "Armas de jugador de Pixel Gun 3D 11.3.1. Cada carpeta es un arma: "
            "<categoria>/<slug>/<slug>.glb junto a su PNG. weapon.json es la ficha. "
            "Busca por id (weapon102), slug (ak-48) o alias único (AK47_Mesh). "
            "No incluye brazos, props de mapa, armas de enemigos ni armas de mech."
        ),
        "path_pattern": "exports/weapons/<category>/<slug>/<slug>.glb",
        "categories": {key: label for key, label in CATEGORIES.values()},
        "counts": dict_counts(records),
        "failures": failures,
        "weapons": records,
        "lookup": {
            "by_id": {item["id"]: item["folder"] for item in records},
            "by_slug": {item["slug"]: item["id"] for item in records},
            "by_alias": unique_aliases,
            "ambiguous_aliases": ambiguous_aliases,
        },
    }
    (output / "catalog.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n")
    (output / "index.json").write_text(json.dumps([
        {
            "id": item["id"], "name": item["name"], "slug": item["slug"],
            "category": item["category"], "kind": item["kind"], "tier": item["tier"],
            "model": item["model"], "status": item["status"],
        }
        for item in records
    ], indent=2, ensure_ascii=False) + "\n")
    verify(output, records)
    print(json.dumps({
        "weapons": len(records),
        "failures": failures,
        "counts": catalog["counts"],
    }, indent=2, ensure_ascii=False))
    return catalog


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "exports/weapons")
    args = parser.parse_args()
    extract(output=args.output)


if __name__ == "__main__":
    main()
