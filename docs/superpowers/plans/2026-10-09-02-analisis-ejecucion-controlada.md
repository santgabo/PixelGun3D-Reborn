# Plan 2 — De ILSpyCmd a la ejecución controlada

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. La ejecución directa es la propuesta; este plan no autoriza instalaciones, modificaciones del juego ni delegación.

**Goal:** Obtener código y recursos analizables, reconstruir el flujo de arranque y producir una ejecución de referencia observable del APK original, o un bloqueo reproducible sustentado en evidencias.

**Architecture:** Entradas preservadas; salidas independientes por corrida; análisis estático antes de ejecutar. ILSpyCmd estudia Mono, AssetRipper/UnityPy estudian datos y JADX/Apktool explican el arranque Android. La prueba dinámica utiliza el APK y OBB originales, no una recompilación del C# recuperado.

**Tech Stack:** ILSpyCmd, UnityPy, AssetRipper, JADX, Apktool, Python estándar para utilidades de inventario/staging, Android SDK/ADB y Android aislado.

**Spec / base documental:** `docs/analisis-tecnologias-ingenieria-inversa.md`. Prerrequisito operativo: `2026-10-09-01-instalacion-verificacion-herramientas.md` en este directorio.

**Estado:** propuesto; todas las tareas de ejecución están pendientes.

## Restricciones globales

- Unity `5.3.7p1`, Mono, `com.pixel.gun3d` versión `11.3.1`/`1191`; no sustituir sus DLL de referencia por versiones modernas.
- Tratar `apk+obb-original/` y `unpacked/` como entradas inmutables. No cambiar permisos ni renombrar archivos dentro de ellas para preparar el laboratorio.
- No recompilar, parchear, firmar, modificar compras/licencias, redirigir servidores ni portar el juego a otro motor en este plan.
- Decompilar no equivale a recuperar las fuentes originales; exportar un proyecto no implica que compile o funcione.
- Analizar offline; ejecutar primero sin salida a Internet. Cualquier apertura posterior de red requiere decisión y alcance separados.
- No usar cuentas personales ni credenciales encontradas en el cliente; sanear cualquier informe compartido.
- Procesar archivos pesados secuencialmente. Mantener margen de disco del plan 1 y no dejar el emulador abierto durante exportaciones masivas.
- Usar estados `PASS`, `PARTIAL`, `BLOCKED` y `NOT_RUN`; nunca convertir ausencia de errores visibles en éxito no verificado.
- Si se crean utilidades, ejecutar primero pruebas sintéticas que fallen por la funcionalidad ausente; después implementar lo mínimo y repetir pruebas. No realizar experimentos destructivos sobre entradas reales.
- No hay Git inicializado: no crear commits ni repositorio automáticamente. Si se autoriza Git posteriormente, excluir entradas, salidas y archivos privados antes de versionar utilidades propias.

## Entradas y salidas previstas

Entradas:

- `unpacked/apk/assets/bin/Data/Managed/`: 27 DLL.
- `unpacked/apk/assets/bin/Data/` y `unpacked/obb/assets/bin/Data/`.
- `unpacked/apk/classes.dex`.
- `apk+obb-original/Pixel Gun 3D [11.3.1].zip`.
- `apk+obb-original/com.pixel.gun3d/main.1191.com.pixel.gun3d.obb`.
- `.lab/toolchain.lock.json` y la matriz del plan 1.

Al ejecutar, crear `RUN` como ruta absoluta de una carpeta nueva `.lab/runs/<fecha-hora-UTC>/`, sin reutilizar ni borrar automáticamente corridas anteriores.

| Ruta relativa a `RUN` | Contenido |
|---|---|
| `inputs/` | APK original extraído por nombre exacto y manifiestos de hashes |
| `managed/` | Listados, C# por ensamblado e IL selectivo |
| `staging/Data/` | Vista conjunta APK/OBB y fragmentos reensamblados |
| `assets/` | Inventarios, muestras exportadas y relaciones |
| `android/jadx/`, `android/apktool/` | Resultados separados de la capa Android |
| `logs/` | Comandos, versiones, stdout/stderr y códigos de retorno |
| `runtime/` | Perfil, capturas y logs privados de ejecución |
| `reports/` | Resultados de la corrida, todavía sujetos a saneamiento |

Documentos publicables, una vez saneados:

- `docs/analysis/mapa-dependencias.md`
- `docs/analysis/flujo-arranque.md`
- `docs/analysis/inventario-recursos.md`
- `docs/analysis/ejecucion-controlada.md`
- `docs/analysis/conclusiones-y-bloqueos.md`

Cada evidencia debe incluir identificador de corrida, versión de herramienta y origen. Las referencias a código deben conservar ensamblado/tipo/método o token; las referencias a assets deben conservar archivo y `path_id`. Nunca usar solo nombres amigables como identificador único.

## Review Focus

1. Salidas que pisan entradas o concatenación alfabética de `.splitN`: pruebas de rutas y orden numérico — tareas 1 y 3.
2. C# parcialmente decompilado tomado como fuente fiable: revisión de errores y contraste selectivo con IL — tarea 2.
3. Confundir `.resource` FSB5 con archivo serializado, o perder sidecars/relaciones: validación por formato y piloto — tareas 3 y 4.
4. APK correcto con OBB incorrecto/incompleto o actividad mal resuelta: hashes, ruta/nombre exactos y manifiesto — tareas 5 y 6.
5. Dispositivo incompatible o red accidentalmente habilitada: puerta `RUNTIME_READY`, prueba de aislamiento y registro antes/después — tarea 6.

---

## Tarea 1 — Fijar entradas y preparar la corrida

**Archivos:** crear `RUN/inputs/manifest.json`, `RUN/logs/run.json` y copia del lock de herramientas; extraer `RUN/inputs/original.apk`.

**Consume:** fuentes originales y capacidades del plan 1. **Produce:** identidad inmutable de entradas y carpeta de salida exclusiva.

- [ ] Leer ambos planes y comprobar capacidades requeridas: tareas 2–5 pueden ejecutarse sin `RUNTIME_READY` si sus herramientas específicas pasan.
- [ ] Crear `RUN` con permisos privados; rechazar una ruta ya existente, dentro de las entradas o resuelta hacia ellas mediante symlinks. Guardar hora UTC y herramientas efectivamente utilizadas.
- [ ] Calcular SHA-256 del ZIP, OBB y todos los archivos de `unpacked`, registrando ruta relativa, tamaño y hash. Guardar el manifiesto fuera de las entradas; leer por bloques, no cargar el OBB en RAM.
- [ ] Extraer únicamente `Pixel Gun 3D [11.3.1].apk` como `RUN/inputs/original.apk`; rechazar nombres de entrada inesperados o rutas que salgan del destino.
- [ ] Comparar hashes de los miembros APK/OBB con sus equivalentes desempaquetados, informando diferencias y entradas faltantes/sobrantes. Si el OBB original no puede abrirse con el formato detectado, parar esa comparación y registrar el bloqueo, sin asumir equivalencia.
- [ ] Verificar versión/paquete con la decodificación Android del plan 1; si los binarios no corresponden al informe, parar y actualizar el diagnóstico antes de seguir.

**Aceptación:** entradas identificadas, APK original disponible fuera del ZIP y divergencias originales/desempaquetado descartadas o explicadas. No se ha escrito en entradas.

## Tarea 2 — Decompilación Mono y mapa de dependencias

**Archivos:** crear `RUN/managed/`, logs asociados y `docs/analysis/mapa-dependencias.md`.

**Consume:** `ILSPY_READY`, las 27 DLL y hashes de tarea 1. **Produce:** cuatro ensamblados de scripts decompilados con inventario de limitaciones.

- [ ] Definir `MANAGED` como ruta absoluta de `unpacked/apk/assets/bin/Data/Managed` y registrar hashes de las DLL utilizadas.
- [ ] Guardar listados de tipos mediante ILSpyCmd y estudiar las dependencias de los cuatro ensamblados de scripts; mantener las 27 DLL disponibles para resolver referencias.
- [ ] Decompilar cada ensamblado secuencialmente a una carpeta propia, capturando código de retorno, stdout y stderr. Patrón contrastado con la ayuda instalada:

```bash
ilspycmd -p -r "$MANAGED" \
  -o "$RUN/managed/Assembly-CSharp" \
  "$MANAGED/Assembly-CSharp.dll"
```

- [ ] Repetir para `Assembly-CSharp-firstpass.dll`, `Assembly-UnityScript.dll` y `Assembly-UnityScript-firstpass.dll`. No mezclar salidas ni usar opciones para ignorar errores.
- [ ] Revisar los logs y las anotaciones de error dentro del C# generado. Crear un registro `ensamblado | tipo/método | error | evidencia | estado`; incluir explícitamente cero errores detectados si corresponde, sin afirmar perfección del código.
- [ ] Analizar `Player_move_c`, `WeaponManager`, `WeaponSounds`, `PhotonNetwork`, `PhotonView` y clases de inicio identificadas. Seguir `Awake`/`Start`, carga de escenas, coroutines y llamadas a plataforma/servicios.
- [ ] Contrastar al menos un método de movimiento, uno de armas y uno de red con su IL, seleccionados por nombre/token tras el inventario. Si una decompilación falla, conservar IL y marcar la interpretación como pendiente.
- [ ] Clasificar subsistemas: `lógica aislable`, `dependiente de Unity`, `puente Android`, `dependiente de backend`; cada clasificación debe citar tipos/métodos concretos.
- [ ] Analizar Photon y SDK adicionales de forma selectiva solo cuando una llamada del flujo lo requiera. No decompilar todo el motor por rutina.

**Aceptación:** cuatro salidas producidas o fallos localizados; mapa con evidencia y separación entre hechos e inferencias. No se intenta compilar ni ejecutar el C# exportado.

## Tarea 3 — Staging Unity y reensamblado probado

**Archivos propios a crear si no existe una utilidad equivalente:** `tools/prepare_unity_data.py`, `tests/test_prepare_unity_data.py`. **Salidas:** `RUN/staging/Data/`, `RUN/staging/manifest.json`.

**Interfaz propuesta:** `prepare_data(apk_data: Path, obb_data: Path, output_data: Path, manifest_path: Path) -> dict`. Devuelve el resumen de inventario; escribe un manifiesto con `relative_path`, `sources`, `kind`, `size`, `sha256`, `validation`. No modifica las entradas. La CLI recibe `--apk-data`, `--obb-data`, `--output-data`, `--manifest` y devuelve código distinto de cero ante una validación fallida.

**Consume:** entradas verificadas. **Produce:** Data completo sin fragmentos sueltos duplicados y con procedencia rastreable.

- [ ] Escribir pruebas `unittest` con temporales sintéticos: índices 0–12 concatenados numéricamente, fragmento intermedio ausente, secuencia que no comienza en 0 y duplicados de índice con distinta escritura.
- [ ] Añadir pruebas: colisión de ruta APK/OBB, archivo ensamblado existente junto a sus fragmentos, destino dentro de origen y ruta/symlink que escape del árbol permitido. Deben fallar sin sobrescribir entradas ni salidas existentes.
- [ ] Añadir pruebas para copia de `Managed`/sidecars, verificación de SHA-256, cabecera Unity v15 con tamaño incorrecto y payload `FSB5` que no debe validarse como archivo serializado Unity.
- [ ] Ejecutar `python3 -m unittest discover -s tests -p 'test_prepare_unity_data.py' -v` y comprobar que los casos nuevos fallan por funcionalidad ausente.
- [ ] Implementar copia/concatenación por bloques a archivos temporales, validación y renombrado final; publicar el manifiesto como completo solo al finalizar. Salidas parciales no reciben marca de éxito. No usar hardlinks ni concatenar por glob alfabético.
- [ ] Repetir pruebas hasta que todas pasen; comprobar que los hashes de entradas sintéticas siguen iguales, incluso en casos de error.
- [ ] Ejecutar sobre el conjunto real: conservar rutas/nombres, unir APK/OBB y mantener `Managed`, `.resource` y todos los archivos auxiliares. No copiar además los `.splitN` consumidos a la vista final.
- [ ] Comparar con el inventario base: 176 grupos, 766 fragmentos; 175 grupos serializados con tamaño coincidente; un grupo `sharedassets94.resource` con firma FSB5; `level0`–`level108` y 7.943 archivos hexadecimales. Cualquier diferencia exige explicación antes del piloto.

**Aceptación:** pruebas pasan, entradas inalteradas, staging sin ambigüedades y cada archivo de salida tiene origen/hash. La validación de tamaño no se presenta como validación semántica de todos los objetos.

## Tarea 4 — Piloto de recursos y correlación con scripts

**Archivos:** crear `RUN/assets/inventory.jsonl`, `RUN/assets/pilot/`, logs y `docs/analysis/inventario-recursos.md`.

**Consume:** `ASSET_TOOLS_READY`, staging y mapa de tarea 2. **Produce:** catálogo inicial, muestras verificadas y relaciones script/objeto.

- [ ] Inventariar objetos por archivo usando la API documentada de la versión fijada de UnityPy. Registrar `source_file`, `path_id`, `class_id/type`, `name`, `unity_version`, `status` y error; procesar por lotes, con puntos de reanudación por archivo.
- [ ] Mantener los archivos dependientes accesibles en el staging completo, pero comenzar por `globalgamemanagers`, `level0` y los recursos referenciados. No interpretar un fallo causado por una muestra incompleta como corrupción.
- [ ] Importar el mismo conjunto en AssetRipper con `Managed` accesible y confirmar Mono/5.3.7p1; registrar versiones y diferencias de interpretación entre herramientas.
- [ ] Seleccionar del inventario una textura, un audio, una malla y un MonoBehaviour relacionado con un script decompilado. Si no están en `level0`, ampliar el conjunto explícitamente; no sustituir una muestra faltante por un éxito supuesto.
- [ ] Exportar esas muestras sin colisiones: ruta de salida derivada de archivo de origen y `path_id`, no solo `m_Name`. Rechazar nombres que escapen de la carpeta de exportación.
- [ ] Validar textura —dimensiones/formato y apertura—; audio —decodificación, duración no nula y escucha breve si está disponible—; malla —vértices, índices válidos y apertura en visor si está disponible—. Registrar limitación si no hay revisión visual/auditiva.
- [ ] Resolver `MonoBehaviour → MonoScript → ensamblado/tipo`; registrar el enlace con el C# y un campo serializado concreto. Si faltan type trees, evaluar TypeTreeGeneratorAPI con las DLL de esta copia; no inventar layouts.
- [ ] Separar estados de objeto: leído, exportado, validado, referencia faltante o error de parser. No tratar un archivo JSON generado como prueba suficiente de fidelidad.
- [ ] Ampliar el inventario por lotes hasta cubrir el conjunto o documentar archivos pendientes. Exportar solo recursos necesarios para entender el arranque/gameplay; posponer una exportación masiva si compromete espacio o no aporta evidencia.

**Aceptación:** piloto reproducible con muestras válidas o fallos concretos, y al menos un enlace recurso/script verificado. El catálogo registra explícitamente su cobertura; no se afirma recuperación íntegra del proyecto.

## Tarea 5 — Android y reconstrucción del flujo de arranque

**Archivos:** crear `RUN/android/jadx/`, `RUN/android/apktool/`, logs y `docs/analysis/flujo-arranque.md`.

**Consume:** `ANDROID_STATIC_READY`, APK original y hallazgos anteriores. **Produce:** secuencia de arranque sustentada en código/manifiesto y guion de prueba dinámica.

- [ ] Decodificar el APK original en un directorio nuevo con Apktool; conservar manifiesto, recursos y smali como evidencia independiente del Java reconstruido.
- [ ] Analizar con JADX el APK/DEX, priorizando `com.pixel.gun3d`, `com.prime31` y `com.unity3d.plugin.downloader`; registrar errores por clase.
- [ ] Confirmar actividad de entrada e intents desde el manifiesto decodificado. Valor esperado: `com.prime31.UnityPlayerNativeActivity`; no lanzar una actividad inventada si difiere.
- [ ] Seguir carga de bibliotecas, comprobación/ubicación del OBB, transferencia a Unity y puntos `UnitySendMessage`/JNI encontrados; citar clase/método o smali cuando Java no sea fiable.
- [ ] Correlacionar Android con scripts de inicio y escenas de tareas 2–4; identificar el primer menú y la primera operación de red solo si hay evidencia. Marcar lo no resuelto.
- [ ] Registrar permisos relevantes, dependencias de servicios y diferencias ARM/x86. No conceder todos los permisos por comodidad ni asumir que un SDK incluido bloquea el arranque.
- [ ] Escribir el guion: iniciar proceso, observar bootstrap, verificar acceso OBB, observar carga Unity/escena, llegar hasta el primer estado estable o bloqueo; prohibir compras/login real.

**Aceptación:** secuencia con evidencia y huecos explícitos; APK/OBB/actividad quedan definidos para la prueba. Si falta una correlación estática, puede investigarse dinámicamente, pero no presentarse como ya confirmada.

## Tarea 6 — Ejecución de referencia sin modificar el juego

**Archivos:** crear `RUN/runtime/` y `docs/analysis/ejecucion-controlada.md`.

**Consume:** `RUNTIME_READY`, APK/OBB originales verificados y guion de tarea 5. **Produce:** sesión reproducible y estado real alcanzado, no promesa de juego funcional.

- [ ] Restaurar dispositivo/snapshot limpio y volver a verificar ABI, almacenamiento, API y aislamiento de salida. Elegir explícitamente el serial ADB de laboratorio y usar `adb -s "$SERIAL"` en todos los comandos.
- [ ] Registrar perfil, herramientas, hashes, hora UTC y ausencia de cuentas. Confirmar que no se apunta a un teléfono personal ni a otro emulador.
- [ ] Instalar `RUN/inputs/original.apk` sin modificarlo. Si ya existe otra instalación, no reemplazarla/desinstalarla automáticamente: restaurar el laboratorio o solicitar decisión.
- [ ] Crear la ruta de expansión y copiar el OBB original con nombre exacto:

```text
/sdcard/Android/obb/com.pixel.gun3d/main.1191.com.pixel.gun3d.obb
```

- [ ] Comprobar tamaño y hash del OBB en dispositivo; si no dispone de utilidad hash, recuperarlo a una salida temporal y compararlo localmente. No usar `staging/Data` en lugar del OBB original.
- [ ] Si Android bloquea instalación o escritura por versión/ABI/almacenamiento, conservar el error y volver a la selección del dispositivo; no parchear manifiesto ni APK para ocultarlo en esta referencia.
- [ ] Iniciar captura completa `adb -s "$SERIAL" logcat -v threadtime` a un archivo privado, conservar PID de la captura y anotar momento de lanzamiento. No filtrar únicamente por Unity o PID: podrían perderse fallos del linker, PackageManager o ActivityManager.
- [ ] Lanzar con `am start -W -n` y el componente confirmado en tarea 5; registrar salida del comando y estado posterior del proceso. Que `am start` devuelva éxito no prueba que Unity haya cargado.
- [ ] Observar hasta 120 segundos iniciales; si hay progreso documentado, ampliar hasta 5 minutos. Son límites de observación, no umbrales universales de fallo del juego.
- [ ] Capturar pantalla/estado en cada hito: actividad creada, runtime Unity iniciado, OBB leído cuando sea observable, escena/menú visible y primer bloqueo. No afirmar lectura OBB si no hay evidencia suficiente.
- [ ] Si hay menú accesible, probar solo navegación básica y una opción claramente local/offline si existe. No iniciar sesión ni realizar compras. Registrar bloqueos de red como resultado, no habilitar Internet para quitarlos.
- [ ] Repetir una vez desde el mismo estado limpio para comprobar reproducibilidad. Permitir como máximo tres intentos si el tercero prueba una hipótesis de entorno explícita; evitar bucles de reinstalación sin hipótesis.
- [ ] Parar el juego con `am force-stop`, finalizar la captura, conservar logs completos privados y crear una copia saneada. Restaurar snapshot y comprobar que no quedan procesos/puertos ni cambios temporales de red sin gestionar.

**Resultado exigido:** `proceso creado`, `Unity iniciado`, `menú alcanzado`, `función local comprobada` o `bloqueado`, con evidencia por cada afirmación. No es necesario alcanzar gameplay para que el experimento produzca un diagnóstico válido; sí es necesario distinguirlo de una ejecución funcional exitosa.

### Clasificación de bloqueos

| Evidencia | Siguiente acción acotada |
|---|---|
| ABI/linker/biblioteca ausente | Contrastar ARM/x86 y elegir dispositivo compatible |
| OBB ausente o ilegible | Revisar nombre, ubicación, hash, permisos y código del downloader |
| Excepción Mono | Vincular stack trace a ensamblado/tipo/método |
| Recurso/script no encontrado | Cruzar con staging, catálogo y relaciones serializadas |
| Red/TLS/autenticación | Documentar dependencia; solicitar experimento de red separado si es necesario |
| Fallo nativo sin explicación | Proponer Ghidra con biblioteca/dirección concretas |
| Flujo invisible pese a logs | Proponer Frida con punto de observación y compatibilidad definidos |
| Error gráfico | Comparar renderer/emulación con cambio de entorno único y registrado |

No instalar herramientas opcionales ni activar red indiscriminadamente ante un fallo.

## Tarea 7 — Integridad, conclusiones y siguiente decisión

**Archivos:** crear `RUN/reports/resultados.json` y `docs/analysis/conclusiones-y-bloqueos.md`; actualizar documentos saneados de tareas anteriores.

**Consume:** evidencias de tareas 1–6. **Produce:** informe que permite decidir la siguiente fase sin exagerar resultados.

- [ ] Recalcular hashes de entradas y comparar con tarea 1. Cualquier diferencia invalida la afirmación de preservación y requiere investigación.
- [ ] Revisar permisos y contenido de informes; retirar claves, tokens, IDs personales y URLs con credenciales antes de compartir. Conservar originales de logs solo en almacenamiento privado.
- [ ] Registrar cobertura: ensamblados procesados, errores de métodos, archivos/objetos inventariados, muestras verificadas y estados dinámicos alcanzados.
- [ ] Separar `confirmado`, `inferido` y `no probado`, con referencia a evidencia para cada conclusión relevante.
- [ ] Ordenar bloqueos por dependencia y coste de la siguiente prueba; escoger una prueba pequeña por bloqueo, no una reimplementación completa.
- [ ] Proponer decisión posterior: preservar APK con runtime embebido, investigar compatibilidad/servicios o diseñar una reimplementación. Ninguna se inicia dentro de este plan.

## Puertas de avance resumidas

1. **G0:** entradas/hash/capacidades identificados → comenzar decompilación.
2. **G1:** DLL legibles y errores localizados → mapa de dependencias.
3. **G2:** staging probado sin pérdida de procedencia → extracción piloto.
4. **G3:** piloto y flujo Android con cobertura explícita → guion dinámico.
5. **G4:** dispositivo/ABI/aislamiento verificados → ejecutar originales.
6. **G5:** ejecución o bloqueo reproducible + integridad final → decidir siguiente investigación.

G4 no se aprueba por haber completado el análisis estático. Un bloqueo reproducible completa el diagnóstico de esa prueba, pero no equivale a aplicación funcional.

## Fuentes operativas

- ILSpyCmd: https://www.nuget.org/packages/ilspycmd
- UnityPy y type trees: https://github.com/K0lb3/UnityPy
- AssetRipper: https://github.com/AssetRipper/AssetRipper
- JADX: https://github.com/skylot/jadx
- Apktool: https://apktool.org/docs/cli-parameters/
- ADB y comandos de actividad: https://developer.android.com/tools/adb
- Nomenclatura y ubicación de expansiones OBB: https://developer.android.com/google/play/expansion-files

Las comprobaciones del informe previo son valores de referencia que se vuelven a validar, no resultados ya ejecutados de este plan.
