# Plan general de extracción de recursos

## Objetivo
Extraer texturas e imágenes en PNG, modelos estáticos en OBJ con sus texturas cuando sea posible, y sonidos en formatos utilizables, a partir del APK y el OBB.

**No incluye:** esqueletos, animaciones, reconstrucción de escenas ni del proyecto de Unity. Los originales deben permanecer intactos.

## Plan y checklist
Las casillas marcadas están completadas. Las demás son los pasos que faltan.

### 1. Preparar el entorno
- [x] Preparar Python y dependencias con **uv**.
- [x] Inicializar **Git**, dejando los archivos del juego y los resultados fuera del repositorio. LFS no es necesario por ahora.

### 2. Preparar e inventariar los archivos
- [x] Leer ambos paquetes y recomponer los archivos fragmentados.
- [x] Identificar las texturas, mallas y sonidos, conservando su procedencia.

### 3. Hacer extracciones de prueba
- [x] Exportar una textura PNG.
- [x] Exportar un modelo estático OBJ con su material y textura.
- [x] Exportar un sonido WAV.

### 4. Validar las muestras
- [x] Comprobar el modelo y su textura en Blender.
- [x] Confirmar con el usuario que el modelo y la imagen se ven y el sonido se escucha correctamente.

### 5. Preparar y ejecutar la extracción masiva
- [ ] Adaptar las herramientas para extraer varios recursos por lotes.
- [ ] Organizar las salidas por tipo y evitar sobrescribir recursos con nombres repetidos.
- [ ] Registrar qué se exportó, de dónde salió y qué falló.
- [ ] Poder reanudar la extracción sin repetir archivos ya comprobados.
- [ ] Probar un lote pequeño y revisar sus resultados antes de escalar.
- [ ] Ejecutar la extracción masiva.
- [ ] Revisar los resultados y entregar un resumen de archivos recuperados, fallos y limitaciones.

## Dónde estamos y qué sigue
**Las etapas 1–4 están completadas para el banco y para la Pixel Gun. La etapa 5 todavía no ha empezado.**

El usuario confirmó las dos muestras: ve el modelo y la textura y escucha el sonido. La del arma está en `exports/samples-weapon/`. Esa confirmación cierra las pruebas; la extracción masiva sigue el checklist de la etapa 5.

El siguiente paso es preparar la extracción por lotes. No hay que repetir el entorno ni el inventario. Las muestras del banco se conservan en `exports/samples/`; los resultados masivos irán en `exports/bulk/`.

## Muestra de arma
Se reutilizó el entorno uv y el inventario ya preparado. No se volvieron a copiar el APK ni el OBB.

- [x] Comprobar de nuevo Python, uv y la lectura de ambos paquetes.
- [x] Elegir en el inventario una malla de arma con material, textura y sonido localizables.
- [x] Exportar la textura PNG, el OBJ con MTL y el WAV del disparo.
- [x] Comprobar el modelo y la textura en Blender, incluido el `.blend` sin el PNG externo.
- [x] Confirmar con el usuario que el modelo y la imagen se ven y el disparo se escucha.

## Documentación de apoyo
- [Entorno uv](../../research/extraction-environment.md).
- [Inventario](../../research/extraction-inventory.md).
- [Muestras y validación](../../research/extraction-samples.md).

Las muestras aprobadas no garantizan que todos los recursos sean exportables ni que su apariencia sea idéntica a la del juego. Cualquier limitación debe quedar registrada.
