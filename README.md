# Pixel Gun 3D — extracción de recursos

Herramientas locales para inventariar y extraer **mallas estáticas, texturas y sonidos** del APK y el OBB suministrados. Sin recuperar esqueletos, animaciones, escenas ni el proyecto original de Unity.

## Showroom 3D — Three.js

Requisitos del visor: Node.js 20.19+ o 22.12+ y un navegador con WebGL. El extractor de Python sigue usando exclusivamente uv.

```bash
npm install
npm run dev
```

Abrir `http://localhost:5173`. El showroom lee directamente `exports/weapons/catalog.json`: selección de modelos GLB con sus texturas, búsqueda por nombre, ID o alias, seis categorías, ordenación y paginación. Incluye cámara orbital con zoom, rotación automática, vista de malla, pantalla completa y reproducción del disparo original cuando existe. La interfaz se adapta a móviles; `/` lleva al buscador.

Los botones **Modelo GLB** y **Textura PNG** descargan los dos archivos por separado. Guardarlos juntos, conservando sus nombres: el GLB referencia la textura PNG.

```bash
npm run build
npm run preview
```

Vite publica solamente `exports/weapons/`, sin copiar las otras exportaciones. La compilación genera `dist/`, con la aplicación y sus recursos locales; no necesita CDN. Si faltan los assets, regenerarlos antes con `uv run --locked -m tools.extract_weapons` (véase `--help` para las opciones). Los recursos del juego y `dist/` no se versionan.

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
# Arma ya exportada en exports/samples-weapon/; otro destino si se repite:
# uv run --locked -m tools.export_samples \
#   --candidate research/evidence/extraction/weapon-sample-candidates.json \
#   --output exports/samples-weapon-check

# Opcional: validar las muestras con Blender ya instalado en macOS.
uv run --locked /Applications/Blender.app/Contents/MacOS/Blender \
  --background --factory-startup --disable-autoexec --offline-mode \
  --python-exit-code 1 --python tools/validate_sample_blender.py

# La extracción masiva reanuda exports/bulk/ y no repite lo ya comprobado.
uv run --locked -m tools.export_bulk --output exports/bulk

# Conversión de los OBJ a GLB. Reanuda exports/gltf/ y no repite un GLB cuyo
# OBJ, MTL y archivo siguen coincidiendo con el SHA256 del diario.
uv run --locked -m tools.export_gltf --output exports/gltf
```

Blender utiliza su Python integrado para `bpy`; se lanza a través de `uv run`, pero no se instala `bpy` en el entorno del extractor. No se necesita Unity Editor.

## Estado

Entorno, inventario, muestras y extracción masiva completados. El usuario confirmó el banco y la Pixel Gun: modelo, textura y sonido de cada una. Los resultados masivos están en `exports/bulk/` y su conversión a GLB, completada, en `exports/gltf/`.

Las muestras del banco están en `exports/samples/`; el modelo autónomo es `validation/School_menu_bench2.blend`. El arma está en `exports/samples-weapon/validation/PixlGun_Mesh.blend`. Los resultados se regeneran localmente y no se versionan.

- [Plan general y checklist](docs/iterations/0001-extraccion-de-recursos.md)
- [Plan de conversión OBJ a GLB](docs/iterations/0002-conversion-obj-a-glb.md)
- [Entorno y comandos uv](research/extraction-environment.md)
- [Inventario](research/extraction-inventory.md)
- [Pruebas de exportación y validación](research/extraction-samples.md)
- [Extracción masiva](research/extraction-bulk.md)
- [Conversión a GLB: resultado](research/extraction-gltf.md)
- [Política de Git y decisión sobre LFS](docs/adr/0001-versionar-herramientas-no-binarios.md)

La extracción no concede derechos de redistribución o reutilización de los recursos del juego.
