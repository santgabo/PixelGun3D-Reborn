# Plan 2 — continuación de recuperación y pruebas

Corrida `20261011T174958Z-completion`, 2026-10-11 UTC. El usuario autorizó instalar las herramientas necesarias y terminar la recuperación y las pruebas pendientes. Esta continuación amplía los resultados del 2026-10-09; no implementa el Plan 3.

`RUN` significa `./.lab/runs/20261011T174958Z-completion/`. Los paquetes, código de terceros, recursos, capturas y registros completos permanecen privados y excluidos de Git.

## Estado de la continuación

La continuación del Plan 2 está cerrada con límites documentados. Las cuatro DLL de scripts se decompilaron y compilan juntas; todos los archivos Unity se inventariaron y se exportaron el proyecto y los recursos. Dos pruebas originales desde instalaciones limpias completaron el campo de tiro y alcanzaron el menú; la primera también comprobó la armería. Farm cargó offline con movimiento, disparo y retorno al menú en un perfil derivado separado. Ocho objetos conservan 332 bytes de campos opacos porque sus tipos no están incluidos en las DLL suministradas. No se afirma haber recuperado las fuentes originales ni un proyecto Unity listo para producir un APK equivalente.

| Pregunta | Resultado y evidencia |
|---|---|
| ¿Están instaladas las herramientas necesarias? | Sí: suite local y proveedores REA verificados. Recibos en `./.lab/private/setup/` y `./.lab/private/runtime-setup/`. |
| ¿Se recuperaron los scripts completos? | Cuatro ensamblados, 1.982 archivos C# y representación IL de 27.881 métodos. Ocho comandos rc0. `RUN/managed/results.json`. |
| ¿Compilan juntos? | Sí: solución .NET 3.5, cuatro proyectos recuperados, rc0, cero errores y 964 advertencias. `RUN/managed/rebuild/RecoveredScripts.slnx`. |
| ¿Quedan archivos Unity por inventariar? | Ninguno: 8.165/8.165 archivos serializados, 490.030 objetos; staging completo de 9.214 archivos. |
| ¿Se exportaron todos los recursos? | AssetRipper importó todo el staging y terminó ambos exports. Los datos ilegibles se conservan y los shaders se exportan como YAML. Ocho objetos requieren definiciones externas para recuperar todos sus campos. |
| ¿Está completo el bytecode Android? | Smali cubre 9.178 clases y 53.088 métodos declarados del DEX, sin faltantes ni extras. Java conserva sus diagnósticos; cuatro métodos necesitan representación alternativa de instrucciones. |
| ¿El OBB usado es auténtico? | Sí: 435.792.640 bytes, huella esperada por el APK coincidente y 9.758 miembros iguales al conjunto usado para la extracción. `RUN/inputs/obb-authentication.json`. |
| ¿Se completó el testeo pendiente? | Sí, con alcance explícito: tutorial/menú repetidos en dos instalaciones limpias; Farm, movimiento, disparo y retorno al menú con perfil derivado. Corridas cerradas. No se probaron todas las escenas ni el multijugador. |

## Suite instalada

Todas las instalaciones nuevas viven en `./.lab/tools/` y `./.lab/venvs/`; no se sustituyeron paquetes del sistema ni se necesitó sudo. Se reutilizan Python 3.14.7, Node 26.8.2 y bubblewrap 0.12.0 de la máquina.

| Herramienta | Versión y función comprobada |
|---|---|
| REA | 6.4.0; inspección real del APK, DLL y método de carga OBB. Registro Codex correcto; esta sesión utiliza la CLI. |
| .NET / ILSpyCmd | SDK 10.0.401 / 11.1.0.9782; exportación completa y compilación conjunta. |
| UnityPy / TypeTreeGeneratorAPI | 1.25.4 / 0.0.10; inventario completo y recuperación de layouts MonoBehaviour. |
| AssetRipper Free | 2.0.0; importación total y exports UnityProject / PrimaryContent. |
| Temurin JDK | 21.0.12.1+1; ejecución real de los proveedores Android. |
| JADX / JADX headless MCP | 1.5.6 / 0.7.1; Java completo y evidencia REA del APK. |
| Apktool | 3.0.3; manifiesto, recursos y Smali completos. |
| SDK / ADB | Command-line Tools 17.0 / Platform-Tools 37.0.1; metadata oficial, conexión y transferencia al guest. |
| Emulador / imagen | 37.2.12 estable / API 25 default x86 r1; KVM y namespace de red comprobados. |

Activación: `source ./.lab/env.sh`. Esa activación únicamente configura rutas; no inicia el juego ni lo aísla. El runtime utiliza el driver privado con bubblewrap y un AVD propio. Java, JADX MCP, ILSpy, Apktool y ADB también están configurados para el servidor REA de Codex. Se conservan respaldos de la configuración previa.

No fue necesario instalar motores de análisis nativo, herramientas de firmware ni herramientas de firma para cerrar estas preguntas. El APK original no se modificó ni se firmó de nuevo.

## Código C# recuperado

| Ensamblado | Archivos C# raw | Métodos IL |
|---|---:|---:|
| Assembly-CSharp | 1.778 | 25.597 |
| Assembly-CSharp-firstpass | 182 | 2.155 |
| Assembly-UnityScript | 11 | 67 |
| Assembly-UnityScript-firstpass | 11 | 62 |

Se preservan los exports originales. Tres proyectos compilan directamente. Para el principal, una copia derivada conserva las máquinas de estado Mono de ocho tipos y corrige tres problemas de representación contrastados contra el IL: un valor opcional enum, un switch de cinco cadenas y seis llamadas a una interfaz genérica. No se cambiaron reglas del juego ni se eliminaron métodos para conseguir compilación. Los catorce `NotImplementedException` encontrados también existen en el IL original.

La solución conjunta referencia los proyectos de scripts recuperados entre sí; Unity y plugins conservan los binarios suministrados. Las 964 advertencias incluyen APIs antiguas y miembros sin uso. Compilar demuestra validez del C# generado; no demuestra equivalencia funcional con las DLL originales. Ninguna DLL recompilada se ejecuta en las pruebas de referencia. Una verificación independiente del controlador recompiló toda la solución con `--no-restore --no-incremental`: rc0, 964 advertencias y cero errores; recibo `RUN/reports/managed-controller-build.json`.

## Recursos Unity

Se reconstruyó el staging a partir del APK y del OBB extraído: 176 grupos split y 766 fragmentos, con procedencia por archivo. El OBB original recuperado después se comparó por streaming con esa procedencia: todos los miembros coinciden por tamaño y SHA-256 y pasan CRC; no hay faltantes, extras ni diferencias.

El inventario cubre 490.030 objetos de todos los archivos serializados. El generador de tipos y lectores alternativos resuelven los antiguos errores de MonoBehaviour. `PlayerSettings` requiere el layout de parche que incluye `muteOtherAudioSources`; la lectura estricta corregida consume sus 325 bytes y coincide en 95 valores con AssetRipper. Tres estructuras UnityScript se recuperaron mediante el lector de AssetRipper.

Se recuperan los campos de 490.022 objetos. Once objetos referencian definiciones no incluidas: siete de ensamblados Editor, tres `StoreKitManager` y uno `LpOwerride`. La lectura estricta demuestra que los tres `StoreKitManager` contienen exactamente 32 bytes de header nativo y cero payload personalizado; no tienen campos serializados perdidos. Los otros ocho conservan 332 bytes opacos además de sus headers conocidos. Una auditoría de todas las 9.489 filas TypeDef de las 27 DLL confirma la ausencia de los tipos consultados. La ausencia de esas definiciones no se presenta como corrupción de los paquetes.

AssetRipper reconoció archivos Unity 5.3.7p1 y 5.3.6p2. Importación total: 21,2 segundos. Exportación UnityProject: 17.254 colecciones, 88,1 segundos. PrimaryContent: 12.067 colecciones, 91,0 segundos. Servidor limitado a loopback y cerrado con rc0. Configuración: `ShaderExportMode=Yaml`, `ExportUnreadableAssets=true`.

Salidas revisables: `RUN/assetripper-unity-project/ExportedProject/` y `RUN/assetripper-primary-content/`. Un export Unity no certifica importación en un Editor ni una compilación del juego. YAML conserva la representación de shaders compilados; no recupera su fuente original.

| Exportación | Archivos | Bytes |
|---|---:|---:|
| UnityProject, incluidos auxiliares | 38.119 | 3.035.269.321 |
| PrimaryContent | 18.844 | 1.830.867.101 |

Los 157 shaders también se extrajeron como referencias expandidas: 5.406 programas GLES/GLES3, con 2.626 payloads únicos, cero `GpuProgramIndex` pendientes y cero marcadores de desensamblado no soportado. Se conserva ShaderLab/GLSL enviado en el paquete; el texto expandido requiere adaptación antes de compilar. Evidencia en `RUN/shader-references-expanded/summary.json` y resultado definitivo de recursos en `RUN/resources-final/refined-summary.json`.

También se validaron todos los medios exportados: 6.542 PNG mediante Pillow, 18 WAV por RIFF/frames, 2.194 OGG por estructura y CRC de todas sus páginas y 7.283 GLB por buffers/accessors e índices. Total: 16.037 archivos, cero fallos, 14,5 segundos, RSS 125 MiB. Esta validación estructural no certifica percepción de audio ni fidelidad visual/animación. `RUN/format-validation/summary.json` conserva el alcance exacto.

AssetRipper emitió 95 diagnósticos de layout en `BulletStackController`/`UnityEngine.UI.InputField`; sus campos se conservaron mediante el lector alternativo y sus JSON, sin atribuir fidelidad completa al proyecto Unity generado. Doce texturas Font del original tienen dimensiones 0×0 y cero bytes de píxeles; explican avisos de exportación y no son evidencia de bytes perdidos.

## Android y evidencia REA

Apktool y JADX completaron sus recorridos con rc0. Los 4.253 Java conservan las anotaciones del decompilador. Cuatro métodos de SDK publicitarios/analítica no tienen una reconstrucción Java estructurada satisfactoria; están conservados en Smali y en modo `simple`, sin marcadores `Method not decompiled` en la representación alternativa. No se afirma que todo ese Java compile ni que hayan desaparecido todas las advertencias.

`RUN/reports/android-bytecode-coverage.json` compara directamente las definiciones del DEX con los Smali: 9.178 clases y 53.088 métodos, cero faltantes y cero extras. `RUN/reports/android-recovery.json` registra los diagnósticos y las representaciones alternativas.

REA observa estáticamente que `UnityPlayer.j()` solo registra un OBB cuando la huella de sus últimos 65.558 bytes aparece en `settings.xml`. El carrier ZIP reconstruido no cumplía esa condición y se conserva como derivado, separado del original; no se utiliza como referencia de gameplay.

| Evidencia REA | Observación |
|---|---|
| `ev_d2bdcf09cf05a302e7a8969e6922c7ab5063f04958587c2d88331318bf0579a5` | Identidad y metadata de Assembly-CSharp; la metadata extensa tiene un límite de representación explícito. |
| `ev_a625c8c123116d80d07eeff0052154a8906cf29416b6695b3d0c976f21a35a2c` | Identidad, manifiesto e inventario Android del APK. |
| `ev_6a5b114cb9646ec9f87a2f2a202fd24104fbd77e0554bf5cfad5ce68200fbeba` | Métodos de UnityPlayer y selección inequívoca de `j(): void`. |
| `ev_24722dc7b887e9eec3857c0b3c19fe3988d24c880ca1b76bbe8357de117e09ae` | Cuerpo de `j(): void`, que condiciona `nativeFile` a la huella del OBB. |

Los JSON completos están en `RUN/reports/rea-*.json`. Estas observaciones son estáticas; la evidencia dinámica se registra por separado.

## Ejecución original

Pruebas con APK y OBB originales, Android 7.1.1/API 25/x86, KVM, AVD exclusivo y namespace sin rutas externas. No hay cuentas personales, servidor ADB compartido ni modificaciones al firewall del host.

La primera corrida confirma boot, API/ABI, Accounts0, aislamiento externo denegado, instalación original y transferencia OBB con SHA-256 coincidente. Cámara, movimiento, salto, recogida de MP5, disparo con tres enemigos eliminados, recarga y entrada física al portal están observados. El juego mostró `Training completed!`, recompensas y Continue. El menú principal y la armería también se observaron; selección de rifle y armadura de recompensa y navegación Pets/Eggs funcionaron localmente.

Durante el tutorial, el descriptor 105 del proceso apuntaba al OBB original y su posición 182.824.623 estaba dentro del payload de un miembro ZIP. Se conservaron mappings, descriptores/offsets y captura simultánea. Es observación de uso del archivo; no se reconstruye una secuencia completa de syscalls.

**Límite observado en una instalación limpia:** el onboarding siguiente obliga a una primera partida multijugador y bloquea Adventure y otros controles hasta completarla. GO queda en `Connecting to server..` dentro del namespace offline. Se descartó el aviso de Google Play Services no soportado del AOSP. En estas dos pruebas no se habilitó Internet ni se alteró el progreso para desbloquear modos. El campo de tiro terminado no se confunde con `FirstMatchCompleted`; no se afirma que todo el single player sea accesible offline desde una instalación limpia.

La segunda corrida partió de la plantilla fría, con paquete inicialmente ausente y cuentas cero. Repitió cámara, movimiento, salto, recogida de MP5, disparo, recarga, tres enemigos eliminados, portal, recompensa y menú. El controlador revisó independientemente las capturas `trial-2/screens/repeat-training-reward-settle.png` y `trial-2/screens/repeat-final-menu-status.png`: muestran `Training completed!` y el menú principal. Ambas corridas terminaron con rc0; sus recibos `runtime-closed.json` registran cierre a las 18:16:07Z y 18:28:28Z.

Se añadió una tercera corrida explícitamente marcada `derived_profile=true`. Preserva el APK/OBB original y respalda el AVD y todas las preferencias antes de modificar exclusivamente el entero de PlayerPrefs `TrainingCompleted_4_4_Sett=1`. Ese valor activa la migración de progreso antiguo prevista en `TrainingController.TrainingCompleted`/`OnGetProgress`; no se editó directamente el Storager cifrado, `FirstMatchCompleted`, moneda ni equipamiento. El juego puede actualizar esos datos mediante su propio código de migración. El TAR, XML antes/después, diff y hashes se conservan en `RUN/runtime/trial-3/`. Una comparación semántica independiente del XML confirma que la modificación manual cambia únicamente ese entero: `controller-fixture-verification.json`, PASS. Esta prueba no acredita que una instalación limpia haya terminado la primera partida multijugador.

**Incidencia del perfil derivado:** su primer arranque dejó pantalla negra y registró `NullReferenceException` en `KillRateCheck.get_tierParam → CheckForBuff → constructor → TrainingController.OnGetProgress → TrainingCompleted → AppsMenu.Awake`. La fuente recuperada consulta `ExpController.Instance.OurTier` desde ese getter; un componente aún no inicializado es la explicación compatible con esa pila, no una lectura instrumentada del valor nulo. El juego había persistido cambios de migración antes de la excepción. Una pausa normal y un único relanzamiento, sin otra edición de preferencias, alcanzaron el menú con Adventure habilitado. La captura `ordinary-relaunch-original-after.png` fue revisada independientemente. El selector Campaign/Arena/Sandbox también se abrió. La migración no se declara libre de fallos.

Ese intento del laboratorio terminó después con exit 137/SIGKILL externo, sin ejecutar el cierre del driver. No quedaron sus procesos. Los eventos de OOM del cgroup y la búsqueda en journal no aportan una causa; no se atribuye a un crash del juego. El último evento completado fue abrir Adventure, antes de procesar la selección de Campaign. Se conservan `trial-3/abrupt-termination.json` y el AVD de ese intento.

Un único reintento, `trial-3-retry`, reutilizó el perfil ya migrado, con los mismos parámetros y sin nuevas ediciones de preferencias. Verificó otra vez la identidad del APK instalado y del OBB, aislamiento y ausencia de cuentas. Campaign abrió Pixelated World y el primer nivel Farm; su presentación y escena 3D cargaron offline. Una primera visita terminó con muerte por enemigos durante la observación. Replay del mismo mapa permitió capturar movimiento hasta la puerta, disparo con munición 7/14 → 6/14 y retícula expandida, y pausa. Quit y los controles Back devolvieron el juego al menú. No se completó el nivel ni se exploraron otros mapas.

| Hito | Resultado | Evidencia privada bajo `RUN/runtime/` |
|---|---|---|
| Tutorial completo y menú, instalación limpia | PASS dos veces | `trial-1/screens/walk-into-portal-after.png`; `trial-2/screens/repeat-training-reward-settle.png`, `repeat-final-menu-status.png` |
| Uso efectivo del OBB original | PASS acotado a observación de descriptor/offset | `trial-1/logs/obb-proc-read-evidence-fixed.stdout`; mappings y captura correlacionada |
| Primera partida multijugador guiada | BLOCKED offline | `trial-1/screens/guided-first-match-go-offline-after.png` |
| Campaign/Farm con perfil derivado | PASS para carga, movimiento y disparo | `trial-3-retry/screens/retry-farm-intro-continue-after.png`, `campaign-movement-live-after.png`, `campaign-shot-live-after.png` |
| Retorno Farm → menú | PASS con perfil derivado | `trial-3-retry/screens/derived-final-status.png` |
| Todas las escenas / fidelidad / APK reconstruido | NOT_RUN | Fuera de esta prueba de referencia; no certificado por el inventario ni la compilación C# |

El controlador revisó independientemente las capturas de Farm, desplazamiento, munición y menú final. El reintento cerró emulador, logcat y ADB; recibo `trial-3-retry/runtime-closed.json`. El AVD activo volvió a la copia anterior al perfil derivado y se conservó el estado derivado final: `runtime/avd-restoration.json`. La copia terminó con rc0, inventario de 17 rutas/tamaños idéntico y SHA-256 coincidente de overlays y archivos menores de 1 GiB; los dos archivos restantes se compararon por ruta/tamaño. La terminación abrupta anterior y el fallo de migración permanecen documentados junto a los éxitos. Informe consolidado: `RUN/reports/runtime-results.json`; cierre: `RUN/runtime/final-cleanup.json`.

## Cierre y alcance restante

Se completó el trabajo autorizado de instalación, recuperación de archivos y pruebas de referencia seleccionadas. Las cifras estáticas, límites y enlaces fueron revisados por un segundo agente sin repetir builds ni hashes masivos. El controlador comprobó que no quedan procesos propios de runtime/AssetRipper ni el listener 58081, y que el namespace del host no cambió: `RUN/reports/controller-final-verification.json`. El servidor REA stdio registrado pertenece al cliente Codex y sigue disponible. El resumen máquina de la continuación está en `RUN/reports/completion-summary.json`; las pruebas conservan sus comandos, códigos, capturas y diagnósticos privados.

El límite de recuperación son las definiciones externas de ocho objetos, junto con las limitaciones de representación Java y YAML descritas arriba. La compilación conjunta de scripts y las pruebas del binario original no certifican un proyecto Unity equivalente ni la ejecución de las DLL reconstruidas. El bloqueo de Adventure en una instalación limpia sigue siendo el onboarding multijugador, y el perfil derivado no lo convierte en un desbloqueo natural. No queda un catálogo de archivos sin procesar; tampoco se declara probado todo el juego.
