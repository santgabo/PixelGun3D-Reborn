# Estado del laboratorio — instalación local

## Actualización suite — 2026-10-11

La [suite necesaria está instalada y verificada](../analysis/continuacion-plan-2-2026-10-11.md#suite-instalada) íntegramente en este worktree: REA 6.4.0, ILSpy, UnityPy con TypeTreeGeneratorAPI, AssetRipper, JDK, JADX CLI/MCP, Apktool y SDK/emulador API25. KVM funciona; dos instalaciones limpias del APK original completaron tutorial y menú offline en un AVD propio. Farm se comprobó con perfil derivado separado y retorno al menú. El runtime está cerrado. No se requirió sudo. `source ./.lab/env.sh` configura la suite local. Las limitaciones de instalación/TCG y cifras posteriores pertenecen al laboratorio histórico; consultar la continuación para el estado vigente.

## Actualización runtime — 2026-10-09

Corrida autorizada **20261009T213202Z**: Emulator **37.2.12.0** y AOSP **Android7.1.1/API25/default/x86 r1** instalados desde artefactos fijados/verificados. Command-line Tools 17.0/ADB 37.0.1 copiados a SDK local independiente; JDK primario solo lectura. SDKmanager genera metadata oficial del emulador, con 398 archivos idénticos al ZIP fijado. **RUNTIME_READY=PASS acotado:** boot/ABI/storage/Accounts0, aislamiento/ADB y restauración comprobados; dos originales al tutorial, cámara en segundo. Sin firewall ni cambios administrativos. TCG sin KVM, lento/no soportado; no implica gameplay completo ni servicios online.

[Perfil actual](./dispositivo-laboratorio.md), [hitos y límites](../analysis/ejecucion-controlada.md), [procedimiento/reversión](./preparacion-runtime.md). Recursos siguen PARTIAL y `STATIC_READY=DEFERRED`; no se instalan herramientas opcionales sin necesidad. Logs originales/código/AVD privados; sin commits ni delegación en esta continuación.

## Historial del Plan 1

Las secciones siguientes conservan el estado y autorizaciones anteriores al Plan 2. Sus referencias a emulador no autorizado o ejecución pendiente son **históricas**, no el estado actual de arriba.

Fecha: 2026-10-09. Tareas 1–4 instaladas con alcance mínimo; continuación acotada de tarea 5: SDK/ADB instalados, runtime aún BLOCKED. Tarea 6 cerrada; parser UnityPy parcial.
La selección está fijada en `./.lab/toolchain.lock.json`. .NET, ILSpyCmd, UnityPy, AssetRipper, JDK, JADX, Apktool, Command-line Tools 17.0 y Platform-Tools/ADB 37.0.1 instalados localmente; no se ha ejecutado el APK. Revisiones por tarea, rondas y suites adicionales canceladas por petición del usuario; la evidencia histórica se conserva.
Resumen y próximos pasos: [avances del laboratorio](./avances.md). Checklist actualizado: [plan 1](../superpowers/plans/2026-10-09-01-instalacion-verificacion-herramientas.md).

`PASS` queda limitado a la prueba realizada; `PARTIAL` indica funcionalidad incompleta; `CLI_READY` verifica la CLI, no el runtime Android. `DEFERRED` indica una capacidad/prueba diferida y `BLOCKED` un impedimento explícito administrativo o técnico. Ninguna herramienta recibe `PASS` solo por existir o por tener metadata correcta.

## Host y presupuesto

- Linux x86_64, Ubuntu 26.04 LTS; Python 3.14.4 existente; glibc 2.43.
- Disco medido en preflight: aproximadamente 219 GiB disponibles (no los 31 GB del contexto histórico); última medida tras SDK/ADB: 216,67 GiB. RAM del inventario: aproximadamente 11 GiB totales, 10 GiB disponibles; swap: 4 GiB.
- .NET, ILSpyCmd, JDK y JADX en PATH opt-in; `JAVA_HOME` local. UnityPy, AssetRipper y Apktool mediante `LAB_UNITYPY_PYTHON`, `LAB_ASSETRIPPER` y `java -jar "$LAB_APKTOOL_JAR"` al cargar `./.lab/env.sh`. SDK/ADB locales en PATH opt-in; su CLI_READY no prueba dispositivo ni ABI.
- Tras tarea 4: 217,01 GiB libres; descargas/extracciones con umbral de 10 GiB y reserva. Procesos CLI terminados.
- Tras tarea 3: 217,8 GiB libres; AssetRipper ~143,5 MiB, venv ~94,3 MiB, muestra ~18,1 MiB. RSS AssetRipper observado ~276 MiB; RAM disponible ~10,0 GiB. UI cerrada.
- `/dev/kvm` existe, pero la sesión no tiene lectura ni escritura. Existencia no equivale a aceleración disponible.
- Política del laboratorio: conservar **al menos 10 GiB libres**; no es requisito del proveedor. Recalcular espacio antes de cada descarga, extracción y exportación; detenerse si el espacio libre menos el pico estimado baja del umbral.
- Reserva conservadora: 5 GiB para herramientas estáticas, cachés y muestras; 12 GiB adicionales para un runtime/AVD limitado. Presupuesto inicial de artefactos seleccionados: aproximadamente 1,11 GiB de descarga; las herramientas estáticas ya se descargaron e instalaron, SDK/ADB se instalaron con autorización de licencia exclusiva; emulador/imagen siguen pendientes de autorización de instalación. Son estimaciones, no expansiones medidas; procesos pesados secuenciales, sin exportar el OBB entero.
- El emulador documenta 16 GB RAM recomendados; el host está por debajo. No se ha probado rendimiento, arranque ni compatibilidad.

## Selección cerrada

| Herramienta | Versión / artefacto | Runtime decidido | Estado | Versión + prueba funcional |
|---|---|---|---|---|
| Python existente | 3.14.4; paquete Ubuntu 3.14.4-1ubuntu0.2 | venv aislado en `./.lab/venvs/unitypy` | PASS | Venv y bootstrap pip fijado rc0; parser tiene limitación separada |
| .NET SDK | 10.0.401 Linux x64 | Incluye Microsoft.NETCore.App 10.0.12 | PASS | Versión/info/runtimes rc0; instalación real de ILSpyCmd rc0 |
| ILSpyCmd | 11.1.0.9782 nupkg | .NET 10, requisito 10.0.0 del runtimeconfig publicado | PASS | Versión rc0; tres clases presentes; WeaponManager legible con referencias Managed originales, rc0 |
| AssetRipper Free | 2.0.0 `AssetRipper_linux_x64.tar.xz` | NativeAOT autocontenido; no necesita .NET externo | PASS | Muestra + 27 Managed, Mono, Unity 5.3.7p1; importación/procesamiento completos; UI loopback cerrada |
| UnityPy | 1.25.4 wheel cp314 Linux x64 | CPython 3.14.4, ABI normal GIL | PARTIAL | Carga Unity 5.3.7p1 y enumera 18 objetos; lectura PlayerSettings falla EOFError, rc1 |
| Eclipse Temurin JDK | 21.0.12.1+1-LTS Linux x64 HotSpot | Bibliotecas nativas glibc | PASS | Versión rc0; ejecuta muestras reales JADX/Apktool rc0 con JAVA_HOME local |
| JADX | 1.5.6 `jadx-1.5.6.zip` | Java >=11 de 64 bits; seleccionado JDK 21 | PASS | Una clase funcional bootstrap Android, 18 métodos y seis imports Android; rc0 |
| Apktool | 3.0.3 `apktool_3.0.3.jar` | Java >=8; seleccionado JDK 21 | PASS | Decode only-manifest rc0, XML legible y cinco valores recuperados; diez avisos de recursos no resueltos |
| Android Command-line Tools | 17.0, build 12700392 | JDK >=17 según launchers; seleccionado JDK 21 | CLI_READY | `sdkmanager --version` y `source.properties` 17.0; rc0, licencia autorizada/aceptada solo SDK/ADB |
| Platform-Tools / ADB | 37.0.1 Linux | Binarios nativos x64; no Java para ADB | INSTALADO / CLI_READY | `adb version` 37.0.1-15733141, protocolo 1.0.41; rc0, sin servidor/dispositivos |
| Android Emulator | 37.2.12 estable Linux x64 | KVM y entorno aislado | BLOCKED | Instalación no autorizada; KVM y aislamiento pendientes |
| Imagen Android | API 25 / Android 7.1, default x86, revisión 1 | Guest x86 de 32 bits; emulador seleccionado | BLOCKED | Instalación no autorizada; ABI efectiva y arranque pendientes |

### Evidencia mínima de instalación — tarea 2

| Herramienta | Estado funcional | Logs privados | Bloqueo |
|---|---|---|---|
| .NET SDK 10.0.401 / runtime 10.0.12 | PASS: instalación local exacta de ILSpyCmd | `./.lab/private/logs/task-2/` (`dotnet-*`, `install-ilspy.*`) | Ninguno |
| ILSpyCmd 11.1.0.9782 | PASS / ILSPY_READY: WeaponManager, Player_move_c y PhotonNetwork listadas; muestra WeaponManager con 108 cuerpos de métodos y referencias Unity legibles | `./.lab/private/logs/task-2/` (`list-classes.*`, `weaponmanager.*`, `sample-inspection.*`); resumen privado `./.lab/smoke/ilspy/validation.json` | Ninguno; firma NuGet no verificada |

Checksums publicados SHA512 Microsoft/NuGet coinciden; SHA256 locales separados en lock. Espacio antes de descargar/extraer superior a 10 GiB con reserva de expansión. Nupkg fijado reutilizado desde evidencia previa e instalado mediante `--tool-path` y `--version`, sin resolución flotante. Stderr de listado/decompilación vacío; sin diagnósticos detectados. C# únicamente en `./.lab/smoke/ilspy/WeaponManager.cs`, privado. No se ejecutó ayuda CLI: las opciones necesarias ya estaban fijadas en el brief. Sin nuevas suites, revisiones ni preflight repetido.

La imagen se selecciona por ABI declarada en la metadata, **no** como prueba de compatibilidad del juego. Build-Tools no son requisito de estas pruebas de lectura; no se han añadido Unity Editor, Gradle, Ghidra, Frida ni IL2CPP tooling.

### Evidencia mínima de instalación — tarea 3

| Herramienta | Estado funcional | Logs privados | Bloqueo / limitación |
|---|---|---|---|
| Python 3.14.4 / UnityPy 1.25.4 | INSTALADO / PARTIAL: pip check rc0, 18 objetos y Unity 5.3.7p1 reconocidos | `./.lab/private/logs/task-3/` (`python-version`, `unitypy-version`, `pip-check`, `pip-freeze`, `unitypy-sample`) | `PlayerSettings.read()` → `EOFError: read_str out of bounds`, rc1; no corrección ni nueva dependencia |
| AssetRipper Free 2.0.0 | PASS: muestra con 27 assemblies, backend Mono, Unity 5.3.7p1; lectura/procesamiento terminados | `./.lab/private/logs/task-3/` (`assetripper-*`); resumen `./.lab/smoke/assets/validation.json` | 7975 avisos de referencias omitidas: limitación de muestra, no prueba de corrupción |

18 artefactos fijados con SHA256 publicado coincidente; hashes locales separados en lock. Bootstrap pip desde wheel, sin ensurepip ni pip global. Dependencias instaladas offline; `tpk_ar` construido Python puro con backend fijado, sin compilación nativa. Funcionalidad individual de dependencias no comprobada, salvo bootstrap/build efectivo; instalación no equivale a certificación de audio/texturas. UI exclusivamente `127.0.0.1:58317` comprobada con `ss`; SIGTERM, shutdown registrado y listener cerrado (código final de proceso no observado). No exportación ni apertura de OBB completo, sin nueva suite/review. `ASSET_TOOLS_READY=PARTIAL` por lectura UnityPy.

### Evidencia mínima de instalación — tarea 4

| Herramienta | Estado funcional | Logs privados | Bloqueo / límite |
|---|---|---|---|
| Temurin JDK 21.0.12.1+1-LTS | PASS: runtime headless de JADX/Apktool | `./.lab/private/logs/task-4/` (`java-version`, `jadx-bootstrap`, `apktool-decode`) | Sin bloqueo nuevo; firma de release no verificada; GUI/compilación no probadas |
| JADX 1.5.6 | PASS: `com.prime31.UnityPlayerNativeActivity`, 18 métodos y seis imports Android | `./.lab/private/logs/task-4/` (`jadx-version`, `jadx-help`, `jadx-bootstrap`, `sample-inspection`) | Sustitución autorizada: `com.pixel.gun3d` solo contiene scaffolding; primera muestra de constantes conservada, sin certificar gameplay |
| Apktool 3.0.3 | PASS: manifiesto legible, package `com.pixel.gun3d`, versión `1191`/`11.3.1`, SDK `15`/`24` | `./.lab/private/logs/task-4/` (`apktool-version`, `apktool-help`, `extract-apk`, `apktool-decode`, `sample-inspection`) | Apktool mueve versión/SDK a `apktool.yml`; diez avisos de atributos de recursos omitidos con `--only-manifest`, no afectan estos cinco valores |

Tres SHA256 oficiales coincidentes, hashes locales separados en lock. Solo la entrada ZIP exacta `Pixel Gun 3D [11.3.1].apk` se extrajo por streaming a `./.lab/smoke/android/original.apk`, validando ruta, duplicados, CRC, tamaño y hash por bloques; sin abrir OBB. Una clase funcional real con `--single-class`, un decode limitado, sin recompilar/firmar/instalar APK. Resumen privado `./.lab/smoke/android/validation.json`. Error local inicial de identificación DEX por assertion de magic incorrecta conservado (rc1), corregido a `dex\\n`; no fallo de herramienta. Sin nuevas suites/reviews ni preflight repetido.

### Diferenciar binario publicado y compilación

- ILSpyCmd requiere .NET 10 por su propio `runtimeconfig`, no por la rama de desarrollo. El SDK se elige para instalación local de herramientas `dotnet tool`.
- AssetRipper publicado usa `PublishAot=true`, invariant globalization y build Ubuntu 22.04. .NET 10 SDK/clang son requisitos para compilarlo, no para ejecutar el binario publicado. NEEDED inspeccionados: libc, libm y loader; arranque real correcto.
- JADX documenta Java >=11 para ejecutar y JDK >=17 para compilar. No instalar Gradle.
- Apktool documenta Java >=8; el tag 3.0.3 confirma target Java 8. Decodificar no exige compilar aapt/aapt2.
- Command-line Tools 17.0 se eligió con aprobación en lugar de 23.0: esta última sustituye sdkmanager por la nueva Android CLI nativa. Los launchers 17.0 se leyeron mediante HTTP Range acotado, sin ejecutarlos; ambos exigen JDK >=17. El nombre oficial `commandlinetools-linux-12700392_latest.zip` incluye `_latest`, pero **build 12700392 + URL completa + checksum** fijan el artefacto, no un alias flotante.

### Python y dependencias

UnityPy y sus dependencias directas/transitivas están fijadas por versión, URL y hash publicado en el lock:
`lz4 4.4.5`, `brotli 1.2.0`, `Pillow 12.3.0`, `texture2ddecoder 1.0.6`, `etcpak 0.9.15`, `astc-encoder-py 0.1.12`, `fmod_toolkit 0.1.3`, `fsspec 2026.9.0`, `attrs 26.1.0`, `tpk_ar 0.2.4`, `archspec 0.2.6`, `pyfmodex 0.7.2`.
Wheels cp314, abi3 o Python puro instalados en Python 3.14.4. `tpk_ar 0.2.4` construido offline desde sdist Python puro, sin compilador nativo. Bootstrap/build locales fijados y utilizados: `pip 26.2.1`, `setuptools 84.0.0`, `wheel 0.48.0`, `packaging 26.3`.

Venv creado `--without-pip`; bootstrap desde wheel pip verificado mediante `PYTHONPATH`, sin paquetes globales. Construcción con `--no-index --no-deps --no-build-isolation`, sin resolución flotante. `pip check` y `pip freeze --all` rc0. Muestra real carga/enumeración correctas; decodificación PlayerSettings parcial.

`fmod_toolkit` incluye FMOD Engine 2.00.10: aviso del wrapper MIT inspeccionado; wheel no aporta aviso específico del vendor. Ninguna aceptación explícita ni cuenta requerida en instalación; no se reprodujo/exportó audio. Licencia/compatibilidad de uso de audio no certificadas.

### Evidencia mínima de instalación — continuación de tarea 5

Command-line Tools 17.0 build 12700392 y Platform-Tools/ADB 37.0.1 instalados exclusivamente desde las URLs exactas del lock en `./.lab/tools/android-sdk`, con SHA1 publicados Google coincidentes y SHA256 locales separados. ZIP inspeccionados (rutas/duplicados/tipos/CRC durante extracción), sin sobrescribir instalaciones inesperadas. Umask 077; descargas, caches y transcript privados bajo `./.lab/private/`. Disco final 232650715136 bytes = 216,67 GiB, superior a 10 GiB con reservas antes de descargar/extraer.

Autorización directa «si» para aceptar exclusivamente `android-sdk-license` del SDK/ADB. Flujo documentado `sdkmanager --licenses`, rc0: se revisó el acuerdo por identificador y texto oficial (solo diferencias de whitespace); únicamente este acuerdo recibió aceptación, los otros siete se rechazaron. Archivo de licencia escrito por sdkmanager, no fabricado. Registro de alcance/texto/hash/transcript en `./.lab/private/logs/task-5-sdk/{license-acceptance.json,android-sdk-license.accepted.txt,licenses-retry1.transcript}`. Primer intento abortó antes de aceptar por comparación demasiado estricta del formato; rc1 conservado, retry corregido rc0.

Shell limpio `env -i … bash --noprofile --norc`, `source ./.lab/env.sh`: rutas reales SDK/ADB/JDK, `sdkmanager --version`, `adb version`, lectura de ambos `source.properties` y `sdkmanager --list_installed` rc0. El listado enumera **solo Platform-Tools 37.0.1**: Command-line Tools extraído manualmente no aporta `package.xml`, aunque CLI y properties prueban 17.0. No se fabricó metadata ni se ejecutó instalación flotante para corregir el listado. Comandos/stdout/stderr/rc en `./.lab/private/logs/task-5-sdk/`. CLI_READY no es conexión/ABI ni PASS funcional runtime.

El controlador confirmó después `sdkmanager --version` → 17.0 y `adb version` → 37.0.1-15733141 desde otro shell limpio; evidencia en `./.lab/private/sdd/2026-10-09-01-instalacion-verificacion-herramientas/controller-sdk-adb-versions.log`. No se repitieron muestras ni se inició servidor ADB.

Sin `adb devices`/`start-server`, emulador, imagen, AVD, Build-Tools, arranque Android ni APK. No nuevas suites/reviews/preflight/snapshots, Git, cambios sistema/KVM/red/home global ni herramientas ajenas. RUNTIME_READY continúa BLOCKED; STATIC_READY DEFERRED y UnityPy PARTIAL se conservan.

## Dependencias nativas y autorizaciones

Fix round 1/5: se completó la lista oficial de instalación manual .NET/Ubuntu 26.04: `ca-certificates`, `libbrotli1`, `libc6`, `libgcc-s1`, `libgssapi-krb5-2`, `libicu78`, `libssl3t64`, `libstdc++6`, `tzdata`, `zlib1g`. Los diez paquetes están instalados según inventario propio de `dpkg-query`; versiones y orígenes de `apt-cache policy` en `./.lab/private/logs/task-1-fix-1/dotnet-native-packages.json`. Los tres antes omitidos son `libbrotli1 1.2.0-3build1` (Ubuntu resolute/main), `libgssapi-krb5-2 1.22.1-2ubuntu4.1` y `tzdata 2026c-0ubuntu0.26.04.1` (Ubuntu resolute-updates/main y resolute-security/main). No se instalaron paquetes. La prueba de cobertura compara selector/lock/inventario con la lista oficial descargada, no con una copia parcial de requisitos. También se conservó el inventario previo de bibliotecas X11, FreeType, fontconfig y ALSA para usos gráficos opcionales de Java. Ninguno de los diez paquetes obligatorios de .NET está pendiente; comprobar NEEDED/importaciones tras descargar, antes de ejecutar. No confundir este preflight con una prueba de carga real. El informe original se conserva como histórico; el fix report (`task-1-fix-1-receipt.json`) corrige su lista incompleta.

Puertas administrativas:
1. **CONCEDIDA y completada solo SDK/ADB**: `android-sdk-license` aceptada por el permiso directo actual. Emulador e imagen siguen **BLOCKED**, sin autorización de instalación; compartir licencia no extiende el permiso. Cualquier licencia distinta requiere autorización nueva.
2. Aprobar acceso administrativo de lectura/escritura a `/dev/kvm` (por ejemplo, grupo KVM y renovación de sesión); no se modificaron grupos/permisos.
3. Aprobar y verificar aislamiento de red y restauración antes de boot del laboratorio o ejecución del APK. No se modificó firewall/red ni se conectó un dispositivo.
4. Si una distribución revela un paquete del sistema ausente o un acuerdo explícito nuevo, registrar paquete/acción exactos y detener esa vía hasta autorización.

## Entradas, evidencia y autenticidad

Se conserva el manifiesto privado de SHA-256 por bloques de 64 MiB: 10.393 archivos de entrada, 1.977.291.055 bytes; además, 9.759 miembros de ZIP/OBB inventariados por el intento recuperado. No se repitió el hash masivo inicial.
Muestra independiente: 27 DLL de `Managed` y una copia de `globalgamemanagers` en `./.lab/samples/`; hashes, tamaños y separación de inodos se verifican frente a entradas/baseline. No hardlinks ni cambios en originales.

Procedencia y validación son diferentes: SHA512 publicado por Microsoft para SDK; SHA256 de releases oficiales GitHub para JADX/Apktool/AssetRipper y API Adoptium para JDK; SHA256 PyPI para paquetes; SHA1 publicado por Google en repository XML para Android. SHA256 local no equivale a autenticidad. NuGet ILSpyCmd y sdist metadata `tpk_ar` se compararon con hashes publicados; firma NuGet no verificada. Tarea 3 verificó SHA256 oficiales de AssetRipper, UnityPy y sus dependencias/bootstrap; hash del wheel construido `tpk_ar` es local y separado del sdist publicado. Tarea 4 verificó SHA256 oficiales de JDK/JADX/Apktool; firma Temurin no verificada. SHA1 publicados Google de Command-line Tools/Platform-Tools coinciden tras descarga; SHA256 locales separados en lock. Emulador/imagen no descargados; no se inventan hashes de proveedor.

Fuentes oficiales: [ILSpy/NuGet](https://www.nuget.org/packages/ilspycmd/11.1.0.9782), [.NET/Ubuntu](https://learn.microsoft.com/en-us/dotnet/core/install/linux-ubuntu-install), [AssetRipper 2.0.0](https://github.com/AssetRipper/AssetRipper/releases/tag/2.0.0), [UnityPy 1.25.4](https://pypi.org/project/UnityPy/1.25.4/), [JADX 1.5.6](https://github.com/skylot/jadx/releases/tag/v1.5.6), [Apktool 3.0.3](https://github.com/iBotPeaches/Apktool/releases/tag/v3.0.3), [Temurin](https://adoptium.net/installation/), [SDK repository](https://dl.google.com/android/repository/repository2-3.xml), [imagen AOSP](https://dl.google.com/android/repository/sys-img/android/sys-img2-3.xml), [emulador](https://developer.android.com/studio/run/emulator).
El lock contiene URLs exactas de artefactos. Logs HTTP, metadata, inventario sin sanear y pruebas se guardan en `./.lab/private/`, con permisos restringidos.

## Uso y capacidades

Cargar explícitamente desde Bash: `source ./.lab/env.sh`. No se modifica `~/.bashrc` ni se activa automáticamente un venv. Rutas locales y caches privados; telemetría .NET/first-run innecesario y comprobación de novedades pip desactivados localmente. No inicia ADB, emulador, UI ni aceptación de licencias.

- `ILSPY_READY`: **PASS**, limitado al listado y a WeaponManager con las referencias Managed originales.
- `ASSET_TOOLS_READY`: **PARTIAL**; AssetRipper PASS para muestra limitada, UnityPy carga/enumera pero falla lectura PlayerSettings.
- `ANDROID_STATIC_READY`: **PASS**, limitado a una clase bootstrap Android y cinco valores del manifiesto recuperados con Apktool; no validación de gameplay ni de recursos completos.
- `STATIC_READY`: **DEFERRED**; cuatro de las cinco herramientas funcionales PASS (ILSpyCmd, AssetRipper, JADX, Apktool); UnityPy PARTIAL impide declarar el conjunto listo.
- SDK/ADB: **CLI_READY / ADB instalado**, limitado al lanzamiento CLI y metadata local; sin prueba de conexión ni ABI.
- `RUNTIME_READY`: **BLOCKED**; independiente del resultado estático.
- La tarea 2 instala .NET/ILSpyCmd y comprueba una muestra, sin afirmar que el juego funcione ni que el contenido completo del OBB sea válido.

## Cierre mínimo — tareas 5/6 y continuación SDK/ADB

El cierre estático se comprobó desde una sesión Bash limpia, `env -i … /bin/bash --noprofile --norc`, cargando solo `source ./.lab/env.sh`: rutas locales y versiones rc0. La continuación SDK/ADB añadió sus comprobaciones CLI desde shells limpios, registradas por el trabajador y el controlador. El intérprete del venv resuelve al Python existente del sistema; `sys.prefix` confirma el venv local. No se repitieron muestras: se reutiliza la evidencia funcional de tareas 2–4. Versiones no otorgan PASS funcional.

| Herramienta | Versión | Prueba real reutilizada | Resultado | Log privado | Bloqueo / límite |
|---|---|---|---|---|---|
| .NET SDK / ILSpyCmd | 10.0.401 (runtime 10.0.12) / 11.1.0.9782 | Instalación exacta; WeaponManager legible, 108 cuerpos | PASS, rc0 | `./.lab/private/logs/task-2/`; cierre `task-6/` | Firma NuGet no verificada |
| Python / UnityPy | 3.14.4 / 1.25.4 | Carga y enumera 18 objetos; lectura PlayerSettings | PARTIAL, rc1 | `./.lab/private/logs/task-3/unitypy-sample.*`; cierre `task-6/` | `EOFError: read_str out of bounds`; decodificación no certificada |
| AssetRipper Free | 2.0.0 | Importación/procesamiento, Mono, Unity 5.3.7p1, 27 Managed | PASS, HTTP rc0 | `./.lab/private/logs/task-3/assetripper-*`; cierre `task-6/` | 7975 referencias omitidas en muestra; rc final UI no observado |
| Temurin JDK / JADX | 21.0.12.1+1-LTS / 1.5.6 | Clase bootstrap Android, 18 métodos | PASS, rc0 | `./.lab/private/logs/task-4/jadx-bootstrap.*`; cierre `task-6/` | No gameplay; firma Temurin no verificada |
| Apktool | 3.0.3 | Decode limitado; cinco valores manifiesto/metadata | PASS, rc0 | `./.lab/private/logs/task-4/apktool-decode.*`; cierre `task-6/` | Diez avisos de recursos omitidos; no recursos completos |
| Command-line Tools / ADB | 17.0 build 12700392 / 37.0.1 | Checks CLI/source.properties rc0; no dispositivo | CLI_READY / INSTALADO | `./.lab/private/logs/task-5-sdk/`; perfil dispositivo | Listado sdkmanager omite cmdline-tools manual; conexión/ABI no comprobadas |
| Emulador / imagen | 37.2.12 / API 25 default x86 r1 | No dispositivo creado/arrancado | BLOCKED | Lock; `./docs/lab/dispositivo-laboratorio.md` | Instalación no autorizada; KVM, ABI efectiva, aislamiento y restauración pendientes |
| Ghidra / Frida / captura avanzada / dnSpyEx / firma (incl. Build-Tools/apksigner) | No seleccionadas/instaladas | Ninguna | DEFERRED | Lock: `deferred_tools` | Exigen pregunta técnica y aceptación concreta |

Disco al cierre histórico tarea 6: **233015799808 bytes = 217,01 GiB libres**; tras SDK/ADB: **232650715136 bytes = 216,67 GiB**, superior a 10 GiB. No procesos AssetRipper/ADB/emulador/QEMU ni servidor Python HTTP detectados; listener AssetRipper cerrado. Nada que detener. Logs stdout/stderr/rc en `./.lab/private/logs/task-6/`. Primer detector de procesos rc1 por coincidir con su propio texto, no por un servidor real; corrección puntual excluye su PID y usa tokens exactos, rc0 (`runtime-processes-final.*`). No se inventa código de salida de la UI previa.

Permitido continuar solo análisis estático acotado de clases Managed, bootstrap DEX/manifiesto y muestra importada por AssetRipper. No habilitar tareas dependientes de decodificación UnityPy, audio/FMOD, OBB completo ni ejecución Android. Perfil y autorizaciones siguientes: `./docs/lab/dispositivo-laboratorio.md`. SDK/ADB ya instalados y `android-sdk-license` aceptada exclusivamente para ellos; eso no habilita runtime ni autoriza emulador/imagen. Reviews/rondas/suites, snapshots/diffs e inventarios masivos adicionales cancelados por petición del usuario; sin aprobación independiente nueva.
