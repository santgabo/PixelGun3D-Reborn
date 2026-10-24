# Pixel Gun 3D — extracción de recursos

Herramientas locales para inventariar y extraer **mallas estáticas, texturas y sonidos** del APK y el OBB suministrados. Sin recuperar esqueletos, animaciones, escenas ni el proyecto original de Unity.

## Entorno: exclusivamente uv

Requisitos: `uv` instalado. Python y dependencias del proyecto se gestionan mediante uv; no usar `pip`, activar manualmente un entorno ni invocar `.venv/bin/python`.

```bash
uv sync --locked
uv run --locked -m unittest discover -s tests -v
uv run --locked tools/check_environment.py
```

`pyproject.toml` declara las dependencias, `uv.lock` fija versiones y hashes, y `.python-version` selecciona Python 3.12.15. Ambos primeros archivos y el pin de Python se versionan; `.venv/` y `.tools/` no. Para añadir dependencias usar `uv add`; para actualizar una, `uv lock --upgrade-package NOMBRE` y volver a validar.

uv crea/reutiliza `.venv/` y descarga un Python gestionado cuando hace falta. La instalación existente de Python está en `.tools/python/`; en un checkout nuevo uv puede usar su almacén gestionado habitual. Para conservar también el intérprete dentro del proyecto, se puede establecer `UV_PYTHON_INSTALL_DIR="$PWD/.tools/python"` antes de sincronizar. No se modifica el Python de macOS.

## Archivos de entrada

Colocar en la raíz, sin renombrar:
- `Pixel Gun 3D [11.3.1].apk`
- `main.1191.com.pixel.gun3d.obb`

No se incluyen en Git ni se descargan del juego. Sus SHA256 esperados están en `research/evidence/extraction/inputs.sha256`. Las comprobaciones y extracciones no modifican estos originales.

## Flujo

```bash
# Estos destinos deben estar libres: no se sobrescriben resultados existentes.
uv run --locked tools/prepare_assets.py
uv run --locked -m tools.inventory_assets
uv run --locked -m tools.export_samples

# Opcional: validar las muestras con Blender ya instalado en macOS.
uv run --locked /Applications/Blender.app/Contents/MacOS/Blender \
  --background --factory-startup --disable-autoexec --offline-mode \
  --python-exit-code 1 --python tools/validate_sample_blender.py
```

Blender utiliza su Python integrado para `bpy`; se lanza a través de `uv run`, pero no se instala `bpy` en el entorno del extractor. No se necesita Unity Editor.

## Estado

Entorno, inventario y muestras completados. El usuario confirmó que el modelo, la textura y el sonido funcionan. La extracción masiva aún no se ha iniciado.

Las muestras existentes están en `exports/samples/`; el modelo autónomo para Blender es `validation/School_menu_bench2.blend`. Los resultados se regeneran localmente y no se versionan.

- [Iteración y pasos pendientes](docs/iterations/0001-extraccion-de-recursos.md)
- [Entorno y comandos uv](research/extraction-environment.md)
- [Inventario](research/extraction-inventory.md)
- [Pruebas de exportación y validación](research/extraction-samples.md)
- [Política de Git y decisión sobre LFS](docs/adr/0001-versionar-herramientas-no-binarios.md)

La extracción no concede derechos de redistribución o reutilización de los recursos del juego.
