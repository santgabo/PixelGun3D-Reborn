# ADR-0001: Proyecto uv y Git sin binarios del juego ni LFS inicialmente

**Estado:** aceptada como configuración inicial; revisar si se decide versionar binarios.
**Fecha:** 2026-10-24 (UTC).

## Contexto
El usuario solicita gestionar Python con uv e iniciar Git. Ya hay un APK de unos 31 MiB, un OBB de unos 416 MiB, aproximadamente 1,4 GiB de datos preparados y exportaciones regenerables. El usuario confirmó las muestras de modelo, textura y sonido.

El OBB supera el límite de 100 MiB por archivo de GitHub. Git LFS permite versionar binarios mediante punteros, pero requiere cliente, almacenamiento remoto compatible y atención a cuotas y permisos de distribución. Git LFS no está instalado actualmente. No hay un remoto elegido ni una necesidad confirmada de versionar los binarios.

## Decisión
1. Gestionar el extractor como proyecto **uv**, con `pyproject.toml`, `uv.lock`, `.python-version`, `uv sync --locked` y `uv run --locked`. Mantener las versiones probadas. El Python integrado de Blender es una excepción necesaria para `bpy`; la aplicación se lanza mediante uv.
2. Inicializar Git local en `main`, sin configurar un remoto ni publicar contenido.
3. Versionar código, pruebas, documentación, metadatos de selección/procedencia y evidencias pequeñas. Incluir el lockfile de uv.
4. Excluir `.venv/`, `.tools/`, `work/`, `exports/`, APK y OBB. Los originales permanecen en disco; se identifican mediante SHA256 versionados. Excluir también cachés y configuración local sensible.
5. **No activar ni instalar Git LFS por ahora.** No configurar filtros LFS mientras los binarios estén fuera del repositorio. `.gitattributes` solo normaliza archivos de texto.

## Alternativas consideradas
- **Git normal con todos los archivos:** descartado; hace crecer el historial y el OBB no se podría subir a GitHub como un blob normal.
- **Git LFS para APK/OBB y todas las exportaciones:** posible, pero introduce almacenamiento/cuotas y versiona datos regenerables sin que se haya pedido. No se hace automáticamente.
- **Código y evidencias en Git; datos locales externos:** elegido para esta etapa. Es sencillo, conserva la procedencia y no añade otra dependencia al equipo.

## Consecuencias
**Ventajas:** repositorio pequeño, clones rápidos, entorno reproducible y ausencia de subidas accidentales de archivos del juego o resultados masivos.

**Costes:** un clon no contiene el juego ni las exportaciones. Para ejecutar el flujo hay que aportar los mismos APK/OBB y regenerar los datos. Git **no es una copia de seguridad de esos binarios**; conservarlos y respaldarlos aparte.

**Revisión futura:** si necesitamos versionar una biblioteca seleccionada de modelos, archivos Blender editados u otros binarios no regenerables, considerar Git LFS antes de su primer commit. Definir patrones selectivos, comprobar servidor/cuotas/licencias e instalar y configurar el cliente. Añadir reglas LFS después no transforma los blobs que ya existan en el historial. Esa ampliación se documentará en otra decisión.

## Referencias
- uv: https://docs.astral.sh/uv/guides/projects/
- Migración sin actualizar dependencias: https://docs.astral.sh/uv/guides/migration/pip-to-project/
- Git init: https://git-scm.com/docs/git-init
- Git LFS: https://git-lfs.com/
- Límites de archivos en GitHub: https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github
