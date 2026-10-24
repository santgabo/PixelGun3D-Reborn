"""Importa y renderiza la muestra en Blender, sin restaurar escenas del juego.

API: https://docs.blender.org/api/current/bpy.ops.wm.html#bpy.ops.wm.obj_import
Lanzar Blender con uv run --locked y las opciones
--background --factory-startup --python-exit-code 1 --python tools/validate_sample_blender.py.
Blender usa su propio Python integrado para bpy.
"""

import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector


def inspect_import(samples):
    manifest = json.loads((samples / "manifest.json").read_text())
    for entry in manifest["files"]:
        with (samples / entry["path"]).open("rb") as source:
            if hashlib.file_digest(source, "sha256").hexdigest() != entry["sha256"]:
                raise ValueError(f"Muestra modificada: {entry['path']}")
    obj_path = samples / manifest["mesh"]["path"]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.obj_import(filepath=str(obj_path), forward_axis="NEGATIVE_Z", up_axis="Y",
                          use_split_objects=False, use_split_groups=False, validate_meshes=True)
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if len(meshes) != 1:
        raise ValueError(f"Se esperaba una malla, se importaron {len(meshes)}")
    obj = meshes[0]
    mesh = obj.data
    expected = manifest["mesh"]
    if len(mesh.vertices) != expected["vertices"] or len(mesh.polygons) != expected["triangles"]:
        raise ValueError("Blender cambió las cantidades de geometría")
    if any(len(p.vertices) != 3 or p.area <= 1e-12 for p in mesh.polygons):
        raise ValueError("Geometría no triangular o degenerada")
    uv_layer = mesh.uv_layers.active
    if uv_layer is None:
        raise ValueError("Blender no importó las UV")
    positions, uv, source_corner_uv = [], [], []
    for line in obj_path.read_text().splitlines():
        parts = line.split()
        if parts and parts[0] == "v":
            x, y, z = map(float, parts[1:])
            positions.append((x, -z, y))  # OBJ -Z/Y -> Blender Y/Z.
        elif parts and parts[0] == "vt":
            uv.append(tuple(map(float, parts[1:])))
        elif parts and parts[0] == "f":
            source_corner_uv.extend(uv[int(corner.split("/")[1]) - 1] for corner in parts[1:])
    imported = [tuple(obj.matrix_world @ vertex.co) for vertex in mesh.vertices]
    for source, destination in zip(sorted(positions), sorted(imported)):
        if any(not math.isfinite(b) or abs(a - b) > 2e-6 for a, b in zip(source, destination)):
            raise ValueError("Posiciones distintas tras convertir los ejes en Blender")
    imported_uv = [tuple(value.uv) for value in uv_layer.data]
    if len(imported_uv) != len(source_corner_uv) or any(
        abs(a - b) > 1e-6 for src, dst in zip(sorted(source_corner_uv), sorted(imported_uv))
        for a, b in zip(src, dst)
    ):
        raise ValueError("UV distintas después de importar en Blender")
    images = []
    for slot in obj.material_slots:
        material = slot.material
        if material is None or material.node_tree is None:
            raise ValueError("No se importó un material con nodos")
        nodes = [node for node in material.node_tree.nodes if node.type == "TEX_IMAGE"]
        for node in nodes:
            image = node.image
            # El importador carga la imagen de forma diferida; consultar size la materializa.
            if image is None or list(image.size) != manifest["texture"]["size"] or not image.has_data:
                raise ValueError("Textura ausente o incorrecta en Blender")
            if Path(bpy.path.abspath(image.filepath)).resolve() != (samples / manifest["texture"]["path"]).resolve():
                raise ValueError("Blender está usando una textura diferente")
            if not node.outputs["Color"].is_linked:
                raise ValueError("La textura no está conectada al material")
            node.interpolation = "Closest"  # La textura elegida usa Point en Unity (filter mode 0).
            images.append(image)
    if len(images) != 1 or any(p.material_index >= len(obj.material_slots) for p in mesh.polygons):
        raise ValueError("Asignación de textura/material inesperada")
    if bpy.data.armatures or bpy.data.actions:
        raise ValueError("La muestra no debe contener esqueletos ni animaciones")
    report = {"vertices": len(mesh.vertices), "triangles": len(mesh.polygons),
              "uv_corners": len(imported_uv), "material_count": len(obj.material_slots),
              "image_size": list(images[0].size), "geometry_and_uv_match_obj": True,
              "texture_loaded_and_connected": True, "armatures": 0, "actions": 0}
    return obj, images, report


def render_preview(obj, images, output):
    scene = bpy.context.scene
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    low = Vector(tuple(min(v[i] for v in corners) for i in range(3)))
    high = Vector(tuple(max(v[i] for v in corners) for i in range(3)))
    center, span = (low + high) / 2, max(high - low)
    camera = bpy.data.objects.new("PreviewCamera", bpy.data.cameras.new("PreviewCamera"))
    scene.collection.objects.link(camera)
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 1.0
    scene.camera = camera
    for name, offset, energy in [("Key", (-1, -1.5, 2), 1400),
                                 ("Fill", (1.5, -0.5, 1), 900), ("Rim", (0, 1.5, 1.5), 1100)]:
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.shape, data.size = energy, "DISK", span
        light = bpy.data.objects.new(name, data)
        scene.collection.objects.link(light)
        light.location = center + Vector(offset) * span
        light.rotation_euler = (center - light.location).to_track_quat("-Z", "Y").to_euler()
    scene.world = bpy.data.worlds.new("PreviewWorld")
    scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.08, 0.08, 0.08, 1)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage = 800, 600, 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "Standard"
    front_rotation, frames = None, {}
    for name, offset in [("School_menu_bench2.png", (1.2, -1.5, 1)),
                         ("School_menu_bench2_back.png", (-1.2, 1.5, 1))]:
        camera.location = center + Vector(offset) * span
        camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.ortho_scale = 1.0
        bpy.context.view_layer.update()
        points = [world_to_camera_view(scene, camera, corner) for corner in corners]
        camera.data.ortho_scale = max(max(abs(p.x - 0.5), abs(p.y - 0.5)) for p in points) * 2 * 1.15
        points = [world_to_camera_view(scene, camera, corner) for corner in corners]
        if any(not (0.05 < p.x < 0.95 and 0.05 < p.y < 0.95 and p.z > 0) for p in points):
            raise ValueError("El encuadre recorta la muestra")
        frames[name] = {"min": [min(p[i] for p in points) for i in (0, 1)],
                        "max": [max(p[i] for p in points) for i in (0, 1)]}
        if front_rotation is None:
            front_rotation = (camera.location.copy(), camera.rotation_euler.copy(), camera.data.ortho_scale)
        scene.render.filepath = str(output / name)
        bpy.ops.render.render(write_still=True)
    camera.location, camera.rotation_euler, camera.data.ortho_scale = front_rotation
    scene.render.filepath = "//School_menu_bench2.png"
    for image in images:
        image.pack()
        image.filepath = "//../textures/school_menu_atlas.png"
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.shading.type = "MATERIAL"
                area.spaces.active.region_3d.view_perspective = "CAMERA"
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "School_menu_bench2.blend"), relative_remap=False)
    return frames


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--samples", type=Path, default=Path(__file__).resolve().parents[1] / "exports/samples")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    samples = args.samples.resolve()
    output = samples / "validation"
    if output.exists():
        raise FileExistsError(f"No se sobrescribe una validación existente: {output}")
    obj, images, report = inspect_import(samples)
    with tempfile.TemporaryDirectory(prefix="validation-", dir=samples) as temporary:
        staging = Path(temporary) / "validation"
        staging.mkdir()
        frames = render_preview(obj, images, staging)
        report.update({"status": "blender_import_and_render_passed", "blender_version": bpy.app.version_string,
                       "preview_frame_bounds": frames, "preview_fully_in_frame": True,
                       "created_at_utc": datetime.now(timezone.utc).isoformat(),
                       "texture_packed_in_blend": all(image.packed_file is not None for image in images),
                       "renderer": bpy.context.scene.render.engine, "preview_filter": "Closest",
                       "game_scene_reconstructed": False, "game_visual_fidelity_not_compared": True,
                       "visual_review_pending": True, "manual_listening_pending": True})
        report["files"] = [{"path": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                            "size_bytes": path.stat().st_size} for path in sorted(staging.iterdir())]
        (staging / "blender-check.json").write_text(json.dumps(report, indent=2) + "\n")
        staging.rename(output)
    print("OK: muestra importada, UV/textura comprobadas, dos renders y .blend guardados")


if __name__ == "__main__":
    main()
