# Iteración 0001 — Extracción de recursos individuales

**Estado:** preparación y muestras completadas; extracción por lotes pendiente.
**Próxima tarea:** T1. Este documento describe trabajo por realizar, no una ejecución ya iniciada.

## Objetivo y alcance
Obtener recursos reutilizables del APK y el OBB: texturas e imágenes PNG, mallas estáticas OBJ con UV y materiales MTL básicos cuando se puedan resolver, y sonidos en WAV, OGG u otro formato adecuado al contenido recuperado.

**Fuera de alcance para todas las tareas:** esqueletos, pesos de deformación, animaciones, reconstrucción de escenas, restauración del proyecto y ejecución del juego. Los personajes se recuperarán en su postura base. No se promete apariencia idéntica al juego ni recuperar archivos fuente originales.

## Base ya completada
- [x] Entorno nativo **uv**, con `pyproject.toml`, `uv.lock`, Python fijado y 26 pruebas superadas. [Entorno y comandos](../../research/extraction-environment.md).
- [x] Originales intactos e identificados por SHA256; fragmentos recompuestos y copias separadas de ambos paquetes.
- [x] Inventario de 9.214 archivos y 490.030 objetos: incluye 4.620 Mesh, 3.340 Texture2D y 1.106 AudioClip. Son objetos catalogados, no recursos únicos ni exportaciones garantizadas. [Resultados y cobertura](../../research/extraction-inventory.md).
- [x] Muestras PNG, OBJ/MTL y WAV exportadas, comprobadas en Blender y **aprobadas por el usuario**. [Validación](../../research/extraction-samples.md).
- [x] Git inicializado; código y evidencias versionados, datos y exportaciones locales. LFS diferido según [ADR-0001](../adr/0001-versionar-herramientas-no-binarios.md).

## Entradas, salidas y reglas
- Originales: `Pixel Gun 3D [11.3.1].apk` y `main.1191.com.pixel.gun3d.obb` en la raíz. Huellas en `research/evidence/extraction/inputs.sha256`.
- Base de trabajo existente: `work/prepared/manifest.json` y `work/inventory/resources.sqlite`, en modo lectura.
- Conservar `exports/samples/` como referencia aprobada; no sobrescribirla.
- Primera selección por lotes: **Texture2D, Mesh y AudioClip**. Registrar expresamente su cobertura; no presentar otros tipos del inventario como exportados.
- Pilotos en `exports/pilot/`; ejecución general en `exports/bulk/`, organizada por tipo. Estado temporal y checkpoints en `work/`.
- Usar `uv run --locked` para las herramientas; Blender conserva su Python integrado y se lanza mediante uv.
- Versionar código, pruebas e informes pequeños; no añadir entradas, entornos ni exportaciones a Git ni activar LFS en esta iteración.

## Contrato común a fijar en T1
**Propuesta de interfaz; todavía no implementada.**

Cada trabajo representa un objeto, identificado por `(paquete, ruta interna, path_id)`, no por su nombre ni por un `file_id` local del catálogo. Debe conservar el hash de la fuente.

Cada exportador recibe esa referencia, sus dependencias resueltas y un destino, y devuelve un resultado con:
- Identidad, nombre original y tipo del recurso; estado `ok`, `failed` o `skipped`.
- Lista de archivos producidos, con ruta, tamaño y SHA256; un recurso puede producir varios archivos.
- Advertencias y motivo concreto de fallo u omisión cuando corresponda.

El coordinador es el único que escribe el manifiesto global y los checkpoints. Los exportadores no modifican el catálogo, los originales ni el estado de otros trabajos. Los nombres de salida deben ser seguros y distinguir recursos homónimos.

## Pasos pendientes
Los módulos y pruebas de lotes siguientes son **nuevos y propuestos**, todavía no implementados. El script `tools/export_samples.py` solo cubre las tres muestras, no el catálogo completo. Cada tarea modifica solo sus archivos; los módulos compartidos se consumen en lectura salvo acuerdo para cambiar el contrato.

### T1 — Fijar contrato, selección e identidad
- [ ] Crear los tipos de entrada/resultado y los helpers de lectura, resolución de dependencias y nombres estables.
- **Depende de:** la base completada.
- **Archivos:** `tools/bulk_common.py`, `tests/test_bulk_common.py`.
- **Cierre:** seleccionar recursos por tipo desde el inventario sin modificarlo; distinguir nombres repetidos; impedir rutas inseguras; conservar fuente y hashes. Fijar el contrato antes de abrir las ramas siguientes.
- **No incluye:** convertir recursos ni ejecutar lotes.

### T2-T — Exportar texturas por recurso
- [ ] Producir PNG y resultado normalizado para cada Texture2D seleccionado.
- **Depende de:** T1.
- **Archivos:** `tools/bulk_textures.py`, `tests/test_bulk_textures.py`.
- **Cierre:** comprobar dimensiones y reapertura del PNG; probar variantes de compresión presentes en el catálogo; registrar formatos no soportados sin abortar otros trabajos.
- **No incluye:** shaders, sprites recortados ni cubemaps; no declararlos cubiertos por esta primera pasada.

### T2-M — Exportar mallas estáticas y materiales
- [ ] Producir OBJ y, cuando sea posible, MTL con referencias a las texturas identificadas por el contrato común.
- **Depende de:** T1; usa el contrato de texturas, sin modificar el módulo T2-T.
- **Archivos:** `tools/bulk_meshes.py`, `tests/test_bulk_meshes.py`.
- **Cierre:** conservar geometría y UV/normales cuando existan; manejar submeshes, materiales múltiples y ausencia de material recuperable. Si solo puede exportarse geometría, dejarlo explícito en las advertencias. Comprobar que las rutas MTL/textura resuelvan en la integración.
- **No incluye:** reconstruir rigs, poses animadas, escenas ni shaders originales.

### T2-A — Exportar audio por recurso
- [ ] Resolver streams y producir los archivos de audio de cada AudioClip seleccionado.
- **Depende de:** T1.
- **Archivos:** `tools/bulk_audio.py`, `tests/test_bulk_audio.py`.
- **Cierre:** validar rangos, formato, canales, frecuencia y duración; contemplar varias muestras por clip y nombres repetidos; registrar codecs no soportados o datos dañados.
- **No incluye:** cambiar el contenido sonoro, normalizar volumen ni asumir que todo audio debe ser PCM de 16 bits.

### T3 — Coordinar lotes, manifiesto y reanudación
- [ ] Crear el comando de lotes que planifica la selección, llama a los exportadores y guarda resultados por recurso.
- **Depende de:** T1; puede desarrollarse en paralelo a T2 usando exportadores simulados en las pruebas.
- **Archivos:** `tools/bulk_export.py`, `tests/test_bulk_export.py`.
- **Cierre:** ofrecer planificación sin exportar, selección explícita, progreso, manifiesto y registro de errores; continuar tras fallos individuales. Probar interrupción/reanudación, reintentos y salidas corruptas o ausentes. No saltar un trabajo como correcto sin verificar sus archivos y hashes. No sobrescribir trabajos ajenos ni ocultar fallos en el resumen final.
- **No incluye:** lógica de conversión por tipo ni ejecución completa del catálogo.

### T4 — Integrar y validar pilotos
- [ ] Ejecutar pilotos pequeños y explícitos por tipo, sin tocar las muestras aprobadas.
- **Depende de:** T3 y el exportador del tipo correspondiente. El piloto de mallas con textura requiere también T2-T.
- **Archivos:** `tests/test_bulk_integration.py`, `research/extraction-bulk.md`; resultados locales en `exports/pilot/`.
- **Cierre:** seleccionar casos representativos del catálogo y registrar cuáles se probaron, sin extrapolar a formatos no examinados. Revisar imágenes, modelos/materiales en Blender y audio. Demostrar reanudación sin repetir resultados verificados y reintento de fallos. Documentar incidencias y resolverlas o limitar explícitamente la cobertura antes de escalar ese tipo.
- **No incluye:** marcar como validado el catálogo completo a partir de unas pocas muestras.

### T5 — Ejecutar y cerrar la extracción general
- [ ] Procesar la selección completa de los tipos que hayan superado T4 y entregar resultados trazables.
- **Depende de:** T4 para cada tipo incluido; cualquier exclusión debe quedar declarada, no silenciosa.
- **Archivos:** resultados en `exports/bulk/`, actualización de `research/extraction-bulk.md` y del estado de esta iteración.
- **Cierre:** comprobar que `ok + failed + skipped` coincide con la selección planificada; revisar muestras de resultados por tipo y formato; entregar manifiesto, errores, cantidades y limitaciones. Confirmar que los originales mantienen sus SHA256 y que Git no contiene binarios ni resultados generados.
- **No incluye:** prometer recuperación del 100 % ni ocultar recursos no exportables.

## Dependencias y coordinación

```text
      ┌─ T2-T (texturas) ─┐
      ├─ T2-M (mallas) ───┤
T1 ───┼─ T2-A (audio) ────┼─ T4 por tipo ─ T5
      └─ T3 (coordinador) ┘
```

- T1 fija la interfaz; después T2-T, T2-M, T2-A y T3 pueden avanzar en archivos separados.
- Un piloto empieza cuando estén listos su coordinador y sus exportadores necesarios; no debe esperar a tipos independientes.
- El responsable de coordinación mantiene este documento y resuelve cambios del contrato común. No editar módulos compartidos simultáneamente desde distintas tareas.
- Ruta de avance: **contrato → exportador/coordinador → piloto validado → ejecución general**. Si una rama se bloquea, registrar el motivo y continuar solo con trabajo que no dependa de ella.

## Criterio de cierre de la iteración
La iteración termina cuando las tareas pendientes tienen resultados comprobados, el lote dispone de procedencia y reanudación verificadas, y existe un informe de cobertura y fallos. Actualizar cada casilla solo con evidencia de su cierre. La recuperación técnica no concede derechos de redistribución ni garantiza recuperar los archivos fuente originales.

**Acción inmediata al retomar:** implementar y probar T1. No repetir la preparación ni las muestras ya aprobadas salvo que cambien sus entradas o herramientas.
