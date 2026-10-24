# Entorno de extracción — proyecto uv

## Estado
**Gestionado íntegramente como proyecto uv.** El usuario confirmó el modelo, la textura y el sonido del banco y de la Pixel Gun. El inventario, las muestras y la extracción masiva están en disco. El detalle de esta última está en [extraction-bulk.md](extraction-bulk.md).

| Componente | Configuración verificada |
| --- | --- |
| Gestor | uv 0.13.1 |
| Python | CPython 3.12.15, pin en `.python-version` |
| Entorno virtual | `.venv/`, gestionado por uv |
| Dependencias directas | UnityPy 1.25.4 y Pillow 13.0.0 |
| Resolución completa | 13 dependencias instaladas, versiones y hashes en `uv.lock` |
| Proyecto | `pyproject.toml`, no empaquetado (`tool.uv.package=false`) |
| Visor | Blender 5.2.3 LTS, ya instalado en `/Applications/Blender.app` |

## Instalar y ejecutar
Desde la raíz:

```bash
uv sync --locked
uv run --locked -m unittest discover -s tests -v
uv run --locked tools/check_environment.py
```

No usar `pip`, activar manualmente `.venv` ni invocar su intérprete directamente. Todos los comandos del extractor pasan por `uv run`; `--locked` falla si hay que modificar el lockfile en vez de cambiar versiones silenciosamente.

uv crea `.venv/` y descarga un Python gestionado si lo necesita. El intérprete existente permanece en `.tools/python/`, también gestionado por uv. En un checkout nuevo puede usarse el almacén habitual de uv; para mantener el intérprete dentro del proyecto:

```bash
export UV_PYTHON_INSTALL_DIR="$PWD/.tools/python"
uv sync --locked
```

No se modifica el Python de macOS. `.venv/`, `.tools/` y los datos generados no se versionan. Se necesita red para descargar Python/paquetes no disponibles en caché, pero no se contactan servicios del juego.

## Dependencias: una única fuente de verdad
- `pyproject.toml`: dependencias directas y configuración.
- `uv.lock`: resolución exacta y hashes; versionado en Git, no editar a mano.
- `.python-version`: versión exacta de Python.
- `uv add NOMBRE`: añadir una dependencia.
- `uv lock --upgrade-package NOMBRE`: actualizar deliberadamente una dependencia y volver a validar.

Los antiguos `requirements-extraction.in` y `requirements-extraction.txt` se importaron mediante `uv add -r ... -c ...` y se retiraron. Se conservaron exactamente las **13 versiones ya validadas**; no se hizo una actualización de librerías. Pillow se declaró directamente porque el código lo importa, en lugar de depender de que UnityPy lo incorpore transitivamente.

## Blender
También se lanza a través de uv:

```bash
uv run --locked /Applications/Blender.app/Contents/MacOS/Blender \
  --background --factory-startup --disable-autoexec --offline-mode \
  --python-exit-code 1 --python tools/validate_sample_blender.py
```

Blender necesita **su Python integrado para `bpy`**. No se instala `bpy` en el entorno uv ni se sustituye ese intérprete interno. uv gestiona el extractor y lanza la aplicación; esta separación es intencionada. No se necesita Unity Editor.

## Validación de la migración
- `uv lock --check` y `uv sync --locked` correctos.
- Las 13 versiones instaladas coinciden con las previas y con el lockfile.
- **26 pruebas automatizadas superadas** en `.venv/` y en un entorno nuevo creado desde cero con `UV_PROJECT_ENVIRONMENT=work/uv-clean-check`.
- En ese entorno nuevo se reexportaron las muestras a un directorio temporal: **PNG, OBJ, MTL y WAV tienen los mismos SHA256 que los archivos aprobados por el usuario**.
- El comprobador de entorno sigue leyendo ambos paquetes, decodifica una textura en memoria y verifica los SHA256 originales.
- Evidencias: `research/evidence/extraction/uv-migration.json` y `environment-check.json`.

El comprobador básico solo lee dos miembros de los paquetes; no sustituye el inventario ni valida todo el catálogo. Los resultados de inventario y muestras están en [extraction-inventory.md](extraction-inventory.md) y [extraction-samples.md](extraction-samples.md).

## Fuentes técnicas
- Migración conservando versiones: https://docs.astral.sh/uv/guides/migration/pip-to-project/
- Gestión de proyectos y `uv run`: https://docs.astral.sh/uv/guides/projects/
- Lock y sincronización: https://docs.astral.sh/uv/concepts/projects/sync/
- Proyecto no empaquetado y entorno independiente: https://docs.astral.sh/uv/concepts/projects/config/
