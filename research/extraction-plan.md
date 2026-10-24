# Plan de extracción de recursos

## Objetivo y alcance acordado
Extraer recursos individuales del APK y el OBB para visualizarlos y utilizarlos fuera del juego:
- Texturas e imágenes en PNG.
- Mallas estáticas en OBJ, con UV y texturas asociadas cuando sea posible; materiales MTL básicos si se pueden resolver.
- Sonidos y música en WAV, OGG u otro formato adecuado al contenido recuperado.

**Fuera de alcance:** esqueletos, pesos de deformación, animaciones, reconstrucción de escenas, restauración del proyecto y ejecución del juego. Los personajes se exportarán en su postura base; no se garantiza la pose ni la apariencia exacta del juego. Exportar una malla no garantiza recuperar automáticamente sus materiales.

## Entradas y estado actual
- `Pixel Gun 3D [11.3.1].apk`
- `main.1191.com.pixel.gun3d.obb`

Ambos son contenedores ZIP con recursos de Unity. La investigación previa identifica Unity 5.3.7p1; existen archivos fragmentados `.splitN` y referencias entre recursos. Las tres muestras ya se exportaron y superaron las comprobaciones técnicas; el modelo también se importó y renderizó en Blender. El usuario confirmó que el modelo, el sonido y la imagen funcionan; las muestras están aprobadas.

**Fase 1 completada:** entorno local con Python 3.12.15 y UnityPy 1.25.4, dependencias fijadas y comprobadas; SHA256 de los originales conservados. Se leyó un recurso de cada paquete y se decodificó una textura del OBB en memoria. Blender 5.2.3 LTS ya está instalado para validar modelos. Comandos, evidencias y límites en [extraction-environment.md](extraction-environment.md).

**Fase 2 completada:** 176 grupos de fragmentos recompuestos, 9.214 archivos preparados y 490.030 objetos catalogados. Se identificaron 4.620 Mesh, 3.340 Texture2D y 1.106 AudioClip. Sin errores de lectura ni referencias rotas dentro de la cobertura seleccionada. Los originales siguen intactos. Catálogo y límites en [extraction-inventory.md](extraction-inventory.md).

**Fases 3–4 completadas y aprobadas por el usuario:** PNG, OBJ/MTL y WAV exportados. Modelo comprobado en Blender, con textura y UV correctas, dos vistas renderizadas y `.blend` autónomo. El usuario confirmó la visualización y la escucha. Resultados en [extraction-samples.md](extraction-samples.md). No se inició la fase 5.

**Infraestructura:** proyecto nativo uv (`pyproject.toml`, `uv.lock`, `uv sync` y `uv run`), conservando las versiones validadas. Política de Git y LFS en [ADR-0001](../docs/adr/0001-versionar-herramientas-no-binarios.md).

## Etapas

### 1. Preparar el entorno
- Revisar Python disponible, compatibilidad de dependencias y espacio en disco.
- Crear un entorno virtual local `.venv`; evaluar UnityPy como lector/exportador y fijar las versiones que funcionen.
- Trabajar sin Unity Editor ni GUI de extracción.
- Registrar hashes de los originales y escribir únicamente en carpetas de trabajo/salida separadas.

### 2. Preparar e inventariar los recursos
- Leer ambos paquetes conservando la procedencia y evitando colisiones entre rutas iguales.
- Recomponer los fragmentos `.splitN` en orden numérico cuando sea necesario.
- Resolver archivos auxiliares y referencias entre recursos de ambos paquetes.
- Generar un inventario por tipo, nombre, archivo de origen e identificador interno; registrar errores de lectura.

### 3. Extracción de prueba
- Exportar una textura PNG.
- Exportar una malla estática OBJ e intentar resolver su textura y material básico.
- Exportar un sonido reproducible.
- Guardar las muestras en `exports/samples/`, junto con su procedencia y limitaciones.

### 4. Validación antes de escalar
- Imagen: abre correctamente y tiene dimensiones y contenido plausibles.
- Modelo: contiene geometría válida y UV cuando existan; comprobar visualmente forma, orientación y asociación de textura en Blender, ya instalado.
- Audio: abre, tiene duración plausible y se escucha correctamente.
- No considerar suficiente que el exportador termine sin errores. Si falla un tipo de recurso, resolver o documentar el bloqueo antes de escalar ese tipo.

### 5. Extracción masiva
- Reutilizar el camino validado para exportar por lotes a `exports/bulk/`, organizado por tipo.
- Usar nombres seguros e identificadores de origen para evitar sobrescrituras.
- Generar un manifiesto que relacione entradas y salidas, con estados de éxito, fallo u omisión y motivos.
- Permitir reanudar y reintentar fallos sin repetir exportaciones verificadas.
- Revisar muestras de los distintos tipos y tamaños, y entregar un resumen de cantidades y limitaciones. No prometer recuperación del 100 %.

## Entregables
- Entorno reproducible y scripts de inventario/exportación.
- Muestras validadas antes de iniciar la extracción masiva.
- Recursos exportados, manifiesto de procedencia y registro de errores.

## Límites
Los originales permanecerán intactos. La fidelidad está limitada por los datos compilados, la compresión, los shaders y las capacidades del exportador; no se recuperan necesariamente archivos fuente originales. La extracción no concede derechos de redistribución o reutilización.

## Próxima acción
Con las muestras aprobadas y la infraestructura preparada, el siguiente trabajo será implementar la etapa 5: extracción por lotes con procedencia, nombres sin colisiones, registro de fallos y reanudación. Todavía no se ha iniciado.
