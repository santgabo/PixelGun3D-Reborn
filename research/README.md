# Pixel Gun 3D: investigación y extracción

## Trabajo actual: recursos individuales
El alcance acordado es extraer **mallas estáticas, texturas e imágenes y sonidos**, sin esqueletos, animaciones ni reconstrucción de escenas o del proyecto. No se necesita Unity Editor; Blender ya está disponible para validar modelos.

- [Plan general y checklist](../docs/iterations/0001-extraccion-de-recursos.md).
- [Fase 1 completada: entorno aislado](extraction-environment.md).
- [Fase 2 completada: inventario y referencias](extraction-inventory.md).
- [Fases 3–4 completadas y muestras aprobadas por el usuario](extraction-samples.md).
- [Fase 5 completada: extracción masiva](extraction-bulk.md).
- [Iteración 0002 completada: conversión OBJ a GLB](extraction-gltf.md).
- [Política de Git y LFS](../docs/adr/0001-versionar-herramientas-no-binarios.md); proyecto gestionado con `uv`.

## Investigación previa: menú y tienda originales en desktop
Lo que sigue conserva la investigación inicial y sus recomendaciones históricas; restaurar el proyecto o las escenas **no forma parte del trabajo actual**.

### Objetivo
Evaluar la recuperación fiel del menú principal y la tienda del APK/OBB suministrados. No implementar interfaces nuevas, mapas ni juego; no asumir que la versión 11.3.1 corresponde a 2015.

### Estado de la primera exploración
- **Respondido estáticamente:** motor Unity 5.3.7p1; ensamblado 11.3.1.1191; jerarquías originales del menú (`level104`) y tienda (`shopngui`) con componentes vinculados; lógica compilada nominal conservada. Fuentes y límites en los dos informes.
- **Parcial:** compatibilidad APK/OBB respaldada por referencias y cabeceras, no probada en ejecución; dependencias de arranque identificadas pero cadena completa y bloqueos de red sin resolver.
- **Pendiente:** esquema exacto de campos NGUI/atlas/fuentes, importación/renderizado desktop, variante inicial del menú y correspondencia con la edición de 2015 recordada.
- **Siguiente paso recomendado:** validar una cadena visual original sprite→atlas→material→textura y una etiqueta→fuente; después seguir los componentes de `level0`/`level1` hasta la activación del menú. No construir una interfaz sustituta.

### Contraste y preservación
El coordinador releyó ambos informes y comprobó contra bytes del APK/OBB la cadena de versión Unity, tamaños de recursos, referencias serializadas `(1,233)` del menú y `(1,324)` de la tienda y SHA256 del ensamblado. Las identidades de scripts corresponden a la tabla decodificada del investigador; no constituyen ejecución ni importación probada.

Se preservaron probes y resultados relevantes en `research/evidence/assets/`, y la identidad de DLLs en `research/evidence/managed-identity.json`. Son parsers exploratorios específicos de esta estructura, no un importador validado. Se omitieron de esa copia el inventario amplio temporal de 484 MB y los binarios extraídos. Las evidencias REA se citan en los informes; no se exportó su ledger completo.

**Recomendación provisional:** evaluar restauración en Unity aprovechando jerarquías y lógica originales, antes que reescribir en Godot o web. No se ha elegido editor destino ni demostrado viabilidad de una compilación desktop. La exploración de recursos terminó en su límite de turnos; el análisis de campos personalizados sigue incompleto.

### Límites
Originales intactos. Sin ejecutar el juego, instalar herramientas ni contactar servicios del juego. Dos investigadores con `openai-codex-account-3/gpt-6.1-sol`; resultados en `assets-findings.md` y `code-findings.md`.
