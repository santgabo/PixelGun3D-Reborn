# Plan 2 — De ILSpyCmd a la ejecución controlada

**Continuación autorizada 2026-10-11, cerrada:** el usuario pidió instalar las herramientas necesarias y terminar recuperación/pruebas usando REA. El [informe vigente](../../analysis/continuacion-plan-2-2026-10-11.md) amplía este plan: suite restaurada localmente, scripts compilados, inventario/exportación total, dos tutoriales completos con KVM y Farm offline con perfil derivado separado. Los límites de campos opacos, fidelidad y onboarding quedan explícitos. Las restricciones de preparación y ausencia de instalaciones/delegación descritas abajo corresponden a la ejecución histórica, antes de esta autorización nueva.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. La ejecución es directa, sin modificaciones del juego ni delegación. El diseño inicial no autorizaba instalaciones; la continuación indicada abajo incorpora el permiso nuevo del usuario para preparación/instalación necesaria, con firewall excluido hasta propuesta y rollback aprobados.

**Goal:** Obtener código y recursos analizables, reconstruir el flujo de arranque y producir una ejecución de referencia observable del APK original, o un bloqueo reproducible sustentado en evidencias.

**Architecture:** Entradas preservadas; salidas independientes por corrida; análisis estático antes de ejecutar. ILSpyCmd estudia Mono, AssetRipper/UnityPy estudian datos y JADX/Apktool explican el arranque Android. La prueba dinámica utiliza el APK y OBB originales, no una recompilación del C# recuperado.

**Tech Stack:** ILSpyCmd, UnityPy, AssetRipper, JADX, Apktool, Python estándar para utilidades de inventario/staging, Android SDK/ADB y Android aislado.

**Spec / base documental:** `./docs/analisis-tecnologias-ingenieria-inversa.md`. Prerrequisito operativo: `2026-10-09-01-instalacion-verificacion-herramientas.md` en este directorio.

**Estado (2026-10-09):** análisis estático/staging y piloto en `20261009T191951Z`; continuación autorizada en `20261009T213202Z` instaló emulador/imagen y verificó aislamiento/restauración sin tocar el firewall. Dos sesiones originales alcanzaron el tutorial offline; cámara verificada en la segunda. La tarea 6 ya no está bloqueada por preparación; el resultado global sigue PARTIAL por cobertura de recursos/flujo pendiente. Resultados: [conclusiones y bloqueos](../../analysis/conclusiones-y-bloqueos.md).

| Tarea | Estado de la corrida | Cobertura real |
|---|---|---|
| 1 — Entradas | PASS | 10.393 hashes; APK/OBB equivalentes a unpacked, identidad revalidada |
| 2 — Mono | PASS acotado | Cuatro ensamblados; tres contrastes IL, cero diagnósticos detectados |
| 3 — Staging | PASS acotado | Pruebas RED→GREEN; 176 grupos/766 fragmentos y procedencia/hash |
| 4 — Recursos | PARTIAL | Cinco archivos/3.524 objetos, muestras técnicas/enlace script; 659 errores y cobertura pendiente explícita |
| 5 — Android | PARTIAL | Decode completo, actividad/OBB/JNI y ruta estática; primer menú/red efectiva pendientes |
| 6 — Runtime | PASS acotado | Android API25/x86 TCG, aislamiento/restauración verificados; dos originales al tutorial, cámara en segundo; menú principal/lectura OBB trazada no probados |
| 7 — Cierre | PASS acotado | Integridad final sin cambios; informes saneados; 33 pruebas sintéticas pasan |

Evidencias privadas en `./.lab/runs/20261009T191951Z/` (estática) y `./.lab/runs/20261009T213202Z/` (dinámica). Entradas/JDK del checkout primario adyacente solo lectura, salidas y nuevo SDK en `step/decompile`. La corrida estática no instaló herramientas; la continuación recibió autorización expresa para instalarlas/preparar el entorno, **excepto firewall sin propuesta/rollback previos**. No se modificó el firewall ni el juego; sin commits ni delegación. Revisión final por el autor. Las tareas parciales no certifican recuperación global ni ejecución funcional.

## Restricciones globales

- Unity `5.3.7p1`, Mono, `com.pixel.gun3d` versión `11.3.1`/`1191`; no sustituir sus DLL de referencia por versiones modernas.
- Tratar `./apk+obb-original/` y `./unpacked/` como entradas inmutables. No cambiar permisos ni renombrar archivos dentro de ellas para preparar el laboratorio.
- No recompilar, parchear, firmar, modificar compras/licencias, redirigir servidores ni portar el juego a otro motor en este plan.
- Decompilar no equivale a recuperar las fuentes originales; exportar un proyecto no implica que compile o funcione.
- Analizar offline; ejecutar primero sin salida a Internet. Cualquier apertura posterior de red requiere decisión y alcance separados.
- No usar cuentas personales ni credenciales encontradas en el cliente; sanear cualquier informe compartido.
- Procesar archivos pesados secuencialmente. Mantener margen de disco del plan 1 y no dejar el emulador abierto durante exportaciones masivas.
- Usar estados `PASS`, `PARTIAL`, `BLOCKED` y `NOT_RUN`; nunca convertir ausencia de errores visibles en éxito no verificado.
- Si se crean utilidades, ejecutar primero pruebas sintéticas que fallen por la funcionalidad ausente; después implementar lo mínimo y repetir pruebas. No realizar experimentos destructivos sobre entradas reales.
- El contexto de planificación no tenía Git; al ejecutar ya existe repositorio y worktree aislado. Mantener la restricción: no crear commits ni repositorio automáticamente. Entradas, salidas y archivos privados quedan excluidos; solo utilidades propias e informes saneados son candidatos a versionado posterior.

## Entradas y salidas previstas

Entradas:

- `./unpacked/apk/assets/bin/Data/Managed/`: 27 DLL.
- `./unpacked/apk/assets/bin/Data/` y `./unpacked/obb/assets/bin/Data/`.
- `./unpacked/apk/classes.dex`.
- `./apk+obb-original/Pixel Gun 3D [11.3.1].zip`.
- `./apk+obb-original/com.pixel.gun3d/main.1191.com.pixel.gun3d.obb`.
- `./.lab/toolchain.lock.json` y la matriz del plan 1.

Al ejecutar, definir `RUN=./.lab/runs/<fecha-hora-UTC>` y crear esa carpeta nueva desde la raíz del repositorio, sin reutilizar ni borrar automáticamente corridas anteriores.

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

- `./docs/analysis/mapa-dependencias.md`
- `./docs/analysis/flujo-arranque.md`
- `./docs/analysis/inventario-recursos.md`
- `./docs/analysis/ejecucion-controlada.md`
- `./docs/analysis/conclusiones-y-bloqueos.md`

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

- [x] Leer ambos planes y comprobar capacidades requeridas: tareas 2–5 pueden ejecutarse sin `RUNTIME_READY` si sus herramientas específicas pasan.
- [x] Crear `RUN` con permisos privados; rechazar una ruta ya existente, dentro de las entradas o resuelta hacia ellas mediante symlinks. Guardar hora UTC y herramientas efectivamente utilizadas.
- [x] Calcular SHA-256 del ZIP, OBB y todos los archivos de `unpacked`, registrando ruta relativa, tamaño y hash. Guardar el manifiesto fuera de las entradas; leer por bloques, no cargar el OBB en RAM.
- [x] Extraer únicamente `Pixel Gun 3D [11.3.1].apk` como `RUN/inputs/original.apk`; rechazar nombres de entrada inesperados o rutas que salgan del destino.
- [x] Comparar hashes de los miembros APK/OBB con sus equivalentes desempaquetados, informando diferencias y entradas faltantes/sobrantes. Si el OBB original no puede abrirse con el formato detectado, parar esa comparación y registrar el bloqueo, sin asumir equivalencia.
- [x] Verificar versión/paquete con la decodificación Android del plan 1; si los binarios no corresponden al informe, parar y actualizar el diagnóstico antes de seguir.

**Aceptación:** entradas identificadas, APK original disponible fuera del ZIP y divergencias originales/desempaquetado descartadas o explicadas. No se ha escrito en entradas.

## Tarea 2 — Decompilación Mono y mapa de dependencias

**Archivos:** crear `RUN/managed/`, logs asociados y `./docs/analysis/mapa-dependencias.md`.

**Consume:** `ILSPY_READY`, las 27 DLL y hashes de tarea 1. **Produce:** cuatro ensamblados de scripts decompilados con inventario de limitaciones.

- [x] Definir `MANAGED` como ruta relativa a la raíz del repositorio: `./unpacked/apk/assets/bin/Data/Managed` y registrar hashes de las DLL utilizadas.
- [x] Guardar listados de tipos mediante ILSpyCmd y estudiar las dependencias de los cuatro ensamblados de scripts; mantener las 27 DLL disponibles para resolver referencias.
- [x] Decompilar cada ensamblado secuencialmente a una carpeta propia, capturando código de retorno, stdout y stderr. Patrón contrastado con la ayuda instalada:

```bash
ilspycmd -p -r "$MANAGED" \
  -o "$RUN/managed/Assembly-CSharp" \
  "$MANAGED/Assembly-CSharp.dll"
```

- [x] Repetir para `Assembly-CSharp-firstpass.dll`, `Assembly-UnityScript.dll` y `Assembly-UnityScript-firstpass.dll`. No mezclar salidas ni usar opciones para ignorar errores.
- [x] Revisar los logs y las anotaciones de error dentro del C# generado. Crear un registro `ensamblado | tipo/método | error | evidencia | estado`; incluir explícitamente cero errores detectados si corresponde, sin afirmar perfección del código.
- [x] Analizar `Player_move_c`, `WeaponManager`, `WeaponSounds`, `PhotonNetwork`, `PhotonView` y clases de inicio identificadas. Seguir `Awake`/`Start`, carga de escenas, coroutines y llamadas a plataforma/servicios.
- [x] Contrastar al menos un método de movimiento, uno de armas y uno de red con su IL, seleccionados por nombre/token tras el inventario. Si una decompilación falla, conservar IL y marcar la interpretación como pendiente.
- [x] Clasificar subsistemas: `lógica aislable`, `dependiente de Unity`, `puente Android`, `dependiente de backend`; cada clasificación debe citar tipos/métodos concretos.
- [x] Analizar Photon y SDK adicionales de forma selectiva solo cuando una llamada del flujo lo requiera. No decompilar todo el motor por rutina.

**Aceptación:** cuatro salidas producidas o fallos localizados; mapa con evidencia y separación entre hechos e inferencias. No se intenta compilar ni ejecutar el C# exportado.

## Tarea 3 — Staging Unity y reensamblado probado

**Archivos propios a crear si no existe una utilidad equivalente:** `./tools/prepare_unity_data.py`, `./tests/test_prepare_unity_data.py`. **Salidas:** `RUN/staging/Data/`, `RUN/staging/manifest.json`.

**Interfaz propuesta:** `prepare_data(apk_data: Path, obb_data: Path, output_data: Path, manifest_path: Path) -> dict`. Devuelve el resumen de inventario; escribe un manifiesto con `relative_path`, `sources`, `kind`, `size`, `sha256`, `validation`. No modifica las entradas. La CLI recibe `--apk-data`, `--obb-data`, `--output-data`, `--manifest` y devuelve código distinto de cero ante una validación fallida.

**Consume:** entradas verificadas. **Produce:** Data completo sin fragmentos sueltos duplicados y con procedencia rastreable.

- [x] Escribir pruebas `unittest` con temporales sintéticos: índices 0–12 concatenados numéricamente, fragmento intermedio ausente, secuencia que no comienza en 0 y duplicados de índice con distinta escritura.
- [x] Añadir pruebas: colisión de ruta APK/OBB, archivo ensamblado existente junto a sus fragmentos, destino dentro de origen y ruta/symlink que escape del árbol permitido. Deben fallar sin sobrescribir entradas ni salidas existentes.
- [x] Añadir pruebas para copia de `Managed`/sidecars, verificación de SHA-256, cabecera Unity v15 con tamaño incorrecto y payload `FSB5` que no debe validarse como archivo serializado Unity.
- [x] Ejecutar `python3 -m unittest discover -s tests -p 'test_prepare_unity_data.py' -v` y comprobar que los casos nuevos fallan por funcionalidad ausente.
- [x] Implementar copia/concatenación por bloques a archivos temporales, validación y renombrado final; publicar el manifiesto como completo solo al finalizar. Salidas parciales no reciben marca de éxito. No usar hardlinks ni concatenar por glob alfabético.
- [x] Repetir pruebas hasta que todas pasen; comprobar que los hashes de entradas sintéticas siguen iguales, incluso en casos de error.
- [x] Ejecutar sobre el conjunto real: conservar rutas/nombres, unir APK/OBB y mantener `Managed`, `.resource` y todos los archivos auxiliares. No copiar además los `.splitN` consumidos a la vista final.
- [x] Comparar con el inventario base: 176 grupos, 766 fragmentos; 175 grupos serializados con tamaño coincidente; un grupo `sharedassets94.resource` con firma FSB5; `level0`–`level108` y 7.943 archivos hexadecimales. Cualquier diferencia exige explicación antes del piloto.

**Aceptación:** pruebas pasan, entradas inalteradas, staging sin ambigüedades y cada archivo de salida tiene origen/hash. La validación de tamaño no se presenta como validación semántica de todos los objetos.

## Tarea 4 — Piloto de recursos y correlación con scripts

**Archivos:** crear `RUN/assets/inventory.jsonl`, `RUN/assets/pilot/`, logs y `./docs/analysis/inventario-recursos.md`.

**Consume:** `ASSET_TOOLS_READY`, staging y mapa de tarea 2. **Produce:** catálogo inicial, muestras verificadas y relaciones script/objeto.

- [x] Inventariar objetos por archivo usando la API documentada de la versión fijada de UnityPy. Registrar `source_file`, `path_id`, `class_id/type`, `name`, `unity_version`, `status` y error; procesar por lotes, con puntos de reanudación por archivo.
- [x] Mantener los archivos dependientes accesibles en el staging completo, pero comenzar por `globalgamemanagers`, `level0` y los recursos referenciados. No interpretar un fallo causado por una muestra incompleta como corrupción.
- [x] Importar el mismo conjunto en AssetRipper con `Managed` accesible y confirmar Mono/5.3.7p1; registrar versiones y diferencias de interpretación entre herramientas.
- [x] Seleccionar del inventario una textura, un audio, una malla y un MonoBehaviour relacionado con un script decompilado. Si no están en `level0`, ampliar el conjunto explícitamente; no sustituir una muestra faltante por un éxito supuesto.
- [x] Exportar esas muestras sin colisiones: ruta de salida derivada de archivo de origen y `path_id`, no solo `m_Name`. Rechazar nombres que escapen de la carpeta de exportación.
- [x] Validar textura —dimensiones/formato y apertura—; audio —decodificación, duración no nula y escucha breve si está disponible—; malla —vértices, índices válidos y apertura en visor si está disponible—. Registrar limitación si no hay revisión visual/auditiva.
- [x] Resolver `MonoBehaviour → MonoScript → ensamblado/tipo`; registrar el enlace con el C# y un campo serializado concreto. Si faltan type trees, evaluar TypeTreeGeneratorAPI con las DLL de esta copia; no inventar layouts.
- [x] Separar estados de objeto: leído, exportado, validado, referencia faltante o error de parser. No tratar un archivo JSON generado como prueba suficiente de fidelidad.
- [x] Ampliar el inventario por lotes hasta cubrir el conjunto o documentar archivos pendientes. Exportar solo recursos necesarios para entender el arranque/gameplay; posponer una exportación masiva si compromete espacio o no aporta evidencia.

**Aceptación:** piloto reproducible con muestras válidas o fallos concretos, y al menos un enlace recurso/script verificado. El catálogo registra explícitamente su cobertura; no se afirma recuperación íntegra del proyecto.

## Tarea 5 — Android y reconstrucción del flujo de arranque

**Archivos:** crear `RUN/android/jadx/`, `RUN/android/apktool/`, logs y `./docs/analysis/flujo-arranque.md`.

**Consume:** `ANDROID_STATIC_READY`, APK original y hallazgos anteriores. **Produce:** secuencia de arranque sustentada en código/manifiesto y guion de prueba dinámica.

- [x] Decodificar el APK original en un directorio nuevo con Apktool; conservar manifiesto, recursos y smali como evidencia independiente del Java reconstruido.
- [x] Analizar con JADX el APK/DEX, priorizando `com.pixel.gun3d`, `com.prime31` y `com.unity3d.plugin.downloader`; registrar errores por clase.
- [x] Confirmar actividad de entrada e intents desde el manifiesto decodificado. Valor esperado: `com.prime31.UnityPlayerNativeActivity`; no lanzar una actividad inventada si difiere.
- [x] Seguir carga de bibliotecas, comprobación/ubicación del OBB, transferencia a Unity y puntos `UnitySendMessage`/JNI encontrados; citar clase/método o smali cuando Java no sea fiable.
- [x] Correlacionar Android con scripts de inicio y escenas de tareas 2–4; identificar el primer menú y la primera operación de red solo si hay evidencia. Marcar lo no resuelto.
- [x] Registrar permisos relevantes, dependencias de servicios y diferencias ARM/x86. No conceder todos los permisos por comodidad ni asumir que un SDK incluido bloquea el arranque.
- [x] Escribir el guion: iniciar proceso, observar bootstrap, verificar acceso OBB, observar carga Unity/escena, llegar hasta el primer estado estable o bloqueo; prohibir compras/login real.

**Aceptación:** secuencia con evidencia y huecos explícitos; APK/OBB/actividad quedan definidos para la prueba. Si falta una correlación estática, puede investigarse dinámicamente, pero no presentarse como ya confirmada.

## Tarea 6 — Ejecución de referencia sin modificar el juego

**Continuación verificada:** `20261009T213202Z`; [perfil/preparación y reversión](../../lab/preparacion-runtime.md), [hitos y límites](../../analysis/ejecucion-controlada.md). Cold-copy del AVD en lugar de Quick Boot; TCG observado en lugar de KVM inaccesible. Mismo estado limpio en dos ensayos, almacenamiento mínimo concedido explícitamente, tutorial como primer estado estable y cámara local comprobada. Presencia/hash OBB confirmados, lectura efectiva no trazada; no se afirmó menú ni gameplay completo. La autorización nueva permite instalar/preparar lo necesario, no abrir Internet ni tocar firewall. Las restricciones originales de no instalar describen la corrida estática y no anulan ese permiso nuevo.

**Archivos:** crear `RUN/runtime/` y `./docs/analysis/ejecucion-controlada.md`.

**Consume:** `RUNTIME_READY`, APK/OBB originales verificados y guion de tarea 5. **Produce:** sesión reproducible y estado real alcanzado, no promesa de juego funcional.

- [x] Restaurar dispositivo/snapshot limpio y volver a verificar ABI, almacenamiento, API y aislamiento de salida. Elegir explícitamente el serial ADB de laboratorio y usar `adb -s "$SERIAL"` en todos los comandos.
- [x] Registrar perfil, herramientas, hashes, hora UTC y ausencia de cuentas. Confirmar que no se apunta a un teléfono personal ni a otro emulador.
- [x] Instalar `RUN/inputs/original.apk` sin modificarlo. Si ya existe otra instalación, no reemplazarla/desinstalarla automáticamente: restaurar el laboratorio o solicitar decisión.
- [x] Crear la ruta de expansión y copiar el OBB original con nombre exacto:

```text
/sdcard/Android/obb/com.pixel.gun3d/main.1191.com.pixel.gun3d.obb
```

- [x] Comprobar tamaño y hash del OBB en dispositivo; si no dispone de utilidad hash, recuperarlo a una salida temporal y compararlo localmente. No usar `staging/Data` en lugar del OBB original.
- [x] Si Android bloquea instalación o escritura por versión/ABI/almacenamiento, conservar el error y volver a la selección del dispositivo; no parchear manifiesto ni APK para ocultarlo en esta referencia.
- [x] Iniciar captura completa `adb -s "$SERIAL" logcat -v threadtime` a un archivo privado, conservar PID de la captura y anotar momento de lanzamiento. No filtrar únicamente por Unity o PID: podrían perderse fallos del linker, PackageManager o ActivityManager.
- [x] Lanzar con `am start -W -n` y el componente confirmado en tarea 5; registrar salida del comando y estado posterior del proceso. Que `am start` devuelva éxito no prueba que Unity haya cargado.
- [x] Observar hasta 120 segundos iniciales; si hay progreso documentado, ampliar hasta 5 minutos. Son límites de observación, no umbrales universales de fallo del juego.
- [x] Capturar pantalla/estado en cada hito: actividad creada, runtime Unity iniciado, OBB leído cuando sea observable, escena/menú visible y primer bloqueo. No afirmar lectura OBB si no hay evidencia suficiente.
- [x] Si hay menú accesible, probar solo navegación básica y una opción claramente local/offline si existe. No iniciar sesión ni realizar compras. Registrar bloqueos de red como resultado, no habilitar Internet para quitarlos.
- [x] Repetir una vez desde el mismo estado limpio para comprobar reproducibilidad. Permitir como máximo tres intentos si el tercero prueba una hipótesis de entorno explícita; evitar bucles de reinstalación sin hipótesis.
- [x] Parar el juego con `am force-stop`, finalizar la captura, conservar logs completos privados y crear una copia saneada. Restaurar snapshot y comprobar que no quedan procesos/puertos ni cambios temporales de red sin gestionar.

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

**Archivos:** crear `RUN/reports/resultados.json` y `./docs/analysis/conclusiones-y-bloqueos.md`; actualizar documentos saneados de tareas anteriores.

**Consume:** evidencias de tareas 1–6. **Produce:** informe que permite decidir la siguiente fase sin exagerar resultados.

- [x] Recalcular hashes de entradas y comparar con tarea 1. Cualquier diferencia invalida la afirmación de preservación y requiere investigación.
- [x] Revisar permisos y contenido de informes; retirar claves, tokens, IDs personales y URLs con credenciales antes de compartir. Conservar originales de logs solo en almacenamiento privado.
- [x] Registrar cobertura: ensamblados procesados, errores de métodos, archivos/objetos inventariados, muestras verificadas y estados dinámicos alcanzados.
- [x] Separar `confirmado`, `inferido` y `no probado`, con referencia a evidencia para cada conclusión relevante.
- [x] Ordenar bloqueos por dependencia y coste de la siguiente prueba; escoger una prueba pequeña por bloqueo, no una reimplementación completa.
- [x] Proponer decisión posterior: preservar APK con runtime embebido, investigar compatibilidad/servicios o diseñar una reimplementación. Ninguna se inicia dentro de este plan.

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
