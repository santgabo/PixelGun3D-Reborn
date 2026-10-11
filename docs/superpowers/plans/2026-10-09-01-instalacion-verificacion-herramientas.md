# Plan 1 — Instalación y comprobación del laboratorio

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. La ejecución directa es la propuesta; no hay autorización de instalación ni de delegación por la mera existencia del plan.

**Goal:** Disponer de un entorno reproducible que decompile Mono, lea recursos Unity y analice Android; preparar por separado un dispositivo de ejecución aislado.

**Architecture:** Herramientas de usuario y entornos aislados, sin Unity Editor ni cambios en los originales. Cada instalación se comprueba primero por versión y después con una prueba funcional pequeña. Se distinguen dos resultados: `STATIC_READY` y `RUNTIME_READY`.

**Tech Stack:** Linux x86_64, .NET/ILSpyCmd, Python/UnityPy, AssetRipper, Java/JADX/Apktool, Android SDK/ADB y Android de laboratorio.

**Spec / base documental:** `./docs/analisis-tecnologias-ingenieria-inversa.md`, especialmente secciones 3, 5, 6 y 10. Complemento: `2026-10-09-02-analisis-ejecucion-controlada.md` en este directorio.

**Estado (2026-10-09):** instalación local realizada y documentada; validación estática parcial y dispositivo de ejecución pendiente. No se ejecutó el juego.

## Avance de ejecución

| Tarea | Avance real | Resultado / pendiente |
|---|---|---|
| 1 — Preflight | Inventario, versiones/URLs/checksums fijados, entorno opt-in y muestras independientes | Completada; selección en `./.lab/toolchain.lock.json` |
| 2 — .NET / ILSpyCmd | Instalados; tres clases listadas y WeaponManager decompilada con referencias originales | `ILSPY_READY=PASS` en la muestra; ayuda CLI omitida en alcance mínimo |
| 3 — UnityPy / AssetRipper | Ambos instalados; AssetRipper importa la muestra Mono/5.3.7p1 | `ASSET_TOOLS_READY=PARTIAL`: UnityPy enumera 18 objetos, pero falla al leer PlayerSettings |
| 4 — Java / JADX / Apktool | Instalados; clase bootstrap real y manifiesto/metadata recuperados | `ANDROID_STATIC_READY=PASS` acotado; no recursos completos ni gameplay |
| 5 — SDK / dispositivo | Command-line Tools 17.0 y ADB 37.0.1 instalados; licencia autorizada exclusivamente para SDK/ADB | `CLI_READY`; emulador, imagen, KVM, ABI, aislamiento y restauración pendientes |
| 6 — Cierre | Versiones/rutas desde shell limpio, matriz, logs y bloqueos documentados | `STATIC_READY=DEFERRED`; `RUNTIME_READY=BLOCKED` |

**Cambios de alcance autorizados:** priorizar instalación y comprobaciones mínimas, sin revisiones por tarea ni suites adicionales; aceptar únicamente `android-sdk-license` para SDK/ADB. Se usó `com.prime31.UnityPlayerNativeActivity` como muestra funcional de JADX porque `com.pixel.gun3d` solo aporta scaffolding en este DEX. Command-line Tools 17.0 estable se fijó en lugar de introducir la nueva CLI de 23.0.

Los checks marcados reflejan pasos ejecutados, **no** certificación integral de una capacidad. Las notas distinguen resultados parciales, pasos omitidos y condiciones que no aplicaron. No se concedieron permisos para paquetes del sistema, KVM, cambios de red, emulador/imagen ni ejecución del APK.

Resumen: [avances del laboratorio](../../lab/avances.md). Evidencia detallada: [estado de herramientas](../../lab/estado-herramientas.md) y [dispositivo de laboratorio](../../lab/dispositivo-laboratorio.md).

## Restricciones globales

- Entradas sin modificar: `./apk+obb-original/` y `./unpacked/`.
- Juego: `com.pixel.gun3d`, versión `11.3.1`, código `1191`; Unity `5.3.7p1`, Mono; ABI ARMv7 y x86 de 32 bits.
- No instalar Unity Editor, IL2CPP tooling, Gradle, Ghidra o Frida como requisitos iniciales.
- No ejecutar scripts descargados mediante `curl | sh`; descargar, inspeccionar y comprobar procedencia antes de ejecutar.
- Elegir distribuciones oficiales estables, no ramas de desarrollo. Resolver y fijar sus versiones exactas en la tarea 1, antes de instalar; no usar referencias flotantes en la repetición del proceso.
- No sustituir el Python del sistema ni instalar paquetes Python globalmente. No añadir repositorios de otra versión de Ubuntu.
- Solicitar autorización antes de usar privilegios, cambiar grupos, instalar paquetes del sistema, aceptar licencias o modificar la red del host.
- Descargar herramientas con Internet no autoriza al APK a acceder a Internet. Son fases diferentes.
- No inicializar Git ni crear commits automáticamente: no se detectó un repositorio Git en esta carpeta.
- Binarios, código decompilado, capturas y credenciales quedan fuera de cualquier publicación. Solo documentación saneada y utilidades propias son candidatos a versionado.

## Contexto comprobado durante la planificación

- Host: Ubuntu 26.04 LTS, x86_64; Python 3.14.4.
- Aproximadamente 31 GB libres y 11 GiB de RAM total; volver a medir al ejecutar.
- `/dev/kvm` existe y hay indicadores AMD-V, pero el usuario actual no tiene acceso de lectura/escritura a KVM. No basta con que exista el dispositivo.
- No se encontraron en PATH .NET, Java, ILSpyCmd, JADX, Apktool, ADB ni Ghidra. Pip no está disponible para el Python inspeccionado.
- Estos datos son una fotografía del entorno, no resultados de instalación.

## Estructura prevista y contratos

Rutas creadas durante la ejecución, salvo componentes de dispositivo que siguen pendientes:

| Ruta | Responsabilidad |
|---|---|
| `./.lab/tools/` | Distribuciones locales de herramientas y descargas verificadas |
| `./.lab/venvs/unitypy/` | Entorno Python aislado |
| `./.lab/env.sh` | Variables de rutas; no se carga automáticamente desde el shell del usuario |
| `./.lab/toolchain.lock.json` | Versiones, rutas, requisitos y procedencia de herramientas |
| `./.lab/private/` | Logs sin sanear y detalles locales de dispositivos; permisos restrictivos |
| `./.lab/smoke/` | Resultados pequeños y desechables de comprobación |
| `./docs/lab/estado-herramientas.md` | Matriz de comprobaciones, bloqueos y capacidad disponible |
| `./docs/lab/dispositivo-laboratorio.md` | Perfil saneado del dispositivo y procedimiento de aislamiento |
| `./docs/lab/avances.md` | Resumen de instalación, capacidades, autorizaciones y próximos pasos |

`toolchain.lock.json`: una entrada por herramienta con `name`, `version`, `platform`, `source_url`, `install_path`, `runtime`, `artifact_sha256`, `verification_source`, `status` y `checked_at`. Para paquetes del sistema registrar versión/origen del paquete en lugar de inventar un hash del instalador. Un SHA-256 calculado localmente identifica un archivo, pero no prueba su autenticidad: distinguirlo de un checksum/firma publicado por el proveedor.

Estados documentados por herramienta: `PASS`, `PARTIAL`, `CLI_READY`, `BLOCKED`, `DEFERRED`. `CLI_READY` distingue las comprobaciones SDK/ADB de la preparación de un dispositivo real. Un ejecutable en PATH no equivale a `PASS`.

Si Git se introduce posteriormente, excluir `./.lab/`, originales y salidas voluminosas antes del primer commit. No crear scripts de instalación generales en esta fase; si hacen falta utilidades nuevas, añadir pruebas antes de su implementación.

## Review Focus

1. Python 3.14 sin wheels compatibles: comprobar dependencias nativas; usar un intérprete aislado compatible si falla, sin alterar el del sistema — tarea 3.
2. Versión de .NET/JDK incorrecta aunque el comando exista: comprobar carga real de una DLL y lectura DEX — tareas 2 y 4.
3. Parser Unity que reconoce una cabecera pero no resuelve objetos: prueba funcional y logs, no solo importación de módulo — tarea 3.
4. Imagen Android de 64 bits sin soporte de aplicaciones de 32 bits o KVM inaccesible: consultar ABI y aceleración efectiva — tarea 5.
5. Consumo excesivo de disco/RAM: inventario previo, salidas pequeñas, ejecución secuencial y criterio de parada — tareas 1, 3 y 6.

---

## Tarea 1 — Preflight y selección reproducible

**Archivos:** crear `./.lab/toolchain.lock.json`, `./.lab/env.sh` y `./docs/lab/estado-herramientas.md`.

**Consume:** host actual e informe base. **Produce:** lista cerrada de versiones/artefactos, rutas y necesidades de autorización.

- [x] Registrar `uname -sm`, `/etc/os-release`, `df -h .`, `free -h`, `id`, herramientas existentes y acceso a `/dev/kvm`.
- [x] Consultar releases oficiales y requisitos de runtime de cada herramienta obligatoria; fijar versión exacta y URL. No confundir los requisitos de compilar desde fuente con los del binario publicado.
- [x] Elegir .NET compatible con ILSpyCmd y Java compatible con JADX/Apktool; identificar dependencias nativas necesarias en Ubuntu antes de instalar.
- [x] Preferir instalación local bajo `./.lab/tools/`; si una herramienta necesita instalación del sistema, registrar motivo, paquetes y aprobación requerida.
- [x] Crear las carpetas locales con archivos privados restringidos; escribir `env.sh` sin credenciales ni cambios automáticos a `~/.bashrc`.
- [x] Registrar presupuesto: mantener al menos 10 GiB libres como margen operativo; detener descargas/exportaciones que lo comprometan. Este umbral es una política del laboratorio, no un requisito del proveedor.
- [x] Preparar una muestra de `Managed` y `globalgamemanagers` por copia independiente o lectura del original; nunca hardlinks que permitan modificar la entrada mediante una salida.

**Aceptación:** cada herramienta obligatoria tiene artefacto y runtime decididos; privilegios pendientes explícitos; no se ha instalado nada sin permiso ni alterado entradas.

## Tarea 2 — .NET e ILSpyCmd

**Archivos:** actualizar lock y matriz; crear `./.lab/smoke/ilspy/`.

**Consume:** selección de tarea 1 y las 27 DLL originales. **Produce:** `ILSPY_READY` con resolución de referencias de este juego.

- [x] Descargar e instalar .NET/ILSpyCmd de las versiones fijadas, con rutas aisladas. Para ILSpyCmd usar instalación local de herramienta o `--tool-path`, con `--version` explícito.
- [x] Ejecutar `dotnet --info`, `dotnet --list-runtimes` e `ilspycmd --version`; guardar salidas y códigos de retorno. `ilspycmd --help` se omitió al reducir las comprobaciones, sin presentarlo como ejecutado.
- [x] Definir `MANAGED="$PWD/unpacked/apk/assets/bin/Data/Managed"` desde la raíz del proyecto.
- [x] Listar clases: `ilspycmd -l c "$MANAGED/Assembly-CSharp.dll"`; comprobar que contiene `WeaponManager`, `Player_move_c` y `PhotonNetwork`.
- [x] Decompilar solo `WeaponManager` con `ilspycmd -r "$MANAGED" -t WeaponManager "$MANAGED/Assembly-CSharp.dll"`, separando stdout/C# de stderr/log.
- [x] Inspeccionar el resultado: clase no vacía, cuerpos de métodos y referencias Unity legibles. No usar opciones que oculten errores ni exigir que el C# compile. Resultado: 108 cuerpos de métodos y cero diagnósticos detectados en la muestra.
- [ ] Si hay referencias no resueltas, comprobar ruta `Managed`, runtime y mensajes; no sustituir DLL del juego por otras descargadas de Internet. **No aplicó:** no se detectaron referencias no resueltas en esta muestra.

**Aceptación:** las tres clases aparecen y la muestra es legible con errores de decompilación ausentes o identificados de forma concreta. Un fallo general mantiene esta capacidad bloqueada.

## Tarea 3 — UnityPy y AssetRipper

**Archivos:** actualizar lock/matriz; crear `./.lab/venvs/unitypy/` y `./.lab/smoke/assets/`.

**Consume:** versión Unity conocida y `globalgamemanagers` con el directorio `Managed` disponible. **Produce:** `ASSET_TOOLS_READY` para comenzar el piloto del plan 2, no una certificación del OBB completo.

- [x] Comprobar soporte de instalación de UnityPy y dependencias para Python 3.14. Se conservaron Python 3.14.4 y dependencias fijadas; no se compilaron dependencias nativas a ciegas. Esto no certifica la decodificación de todos los objetos.
- [x] Crear el venv con pip disponible e instalar la versión fijada de UnityPy. Guardar `python --version`, versión del paquete, `pip check` y congelación de dependencias.
- [x] En un proceso Python separado, cargar una copia de `globalgamemanagers`, enumerar tipos/objetos y confirmar que detecta `5.3.7p1`. Resultado: 18 objetos; **lectura parcial**, `PlayerSettings.read()` falla con `EOFError: read_str out of bounds`.
- [x] Instalar AssetRipper para Linux x86_64 desde la distribución fijada; comprobar requisitos y forma de inicio en su documentación de esa release.
- [x] Abrir la interfaz solamente en loopback. UI comprobada con `ss` en `127.0.0.1`; no expuesta a la LAN.
- [x] Importar la muestra junto con `Managed`, registrar detección de versión/backend y errores. AssetRipper reconoce Mono/5.3.7p1 y procesa la muestra con 27 DLL; las referencias omitidas se registran como limitación, no corrupción.
- [x] Cerrar ambos procesos al terminar, medir disco/RAM y conservar logs. Sin OBB completo ni exportación masiva; listener AssetRipper cerrado. Código final de la UI no observado, sin inventarlo.

**Aceptación:** ambos programas arrancan y reconocen contenido real; quedan identificadas las dependencias necesarias para el piloto. Si solo uno funciona, registrar capacidad parcial, no `ASSET_TOOLS_READY` completo. TypeTreeGeneratorAPI se instala únicamente si el piloto demuestra su necesidad.

## Tarea 4 — Java, JADX y Apktool

**Archivos:** actualizar lock/matriz; crear `./.lab/smoke/android/`.

**Consume:** `classes.dex` y APK original contenido en el ZIP. **Produce:** `ANDROID_STATIC_READY`.

- [x] Instalar el JDK y distribuciones fijadas de JADX/Apktool sin reemplazar otras instalaciones del usuario; establecer `JAVA_HOME` local.
- [x] Ejecutar `java -version`, `jadx --version` y `java -jar "$LAB_APKTOOL_JAR" --version`; conservar ayuda CLI necesaria de las versiones instaladas.
- [x] Con JADX decompilar una clase real con `--single-class`; comprobar paquete, métodos y referencias Android. **Sustitución autorizada:** `com.prime31.UnityPlayerNativeActivity`, con 18 métodos y seis imports Android; `com.pixel.gun3d` solo aporta scaffolding en este DEX. No valida gameplay.
- [x] Extraer por nombre exacto `Pixel Gun 3D [11.3.1].apk` del ZIP a `./.lab/smoke/android/original.apk`; rechazar extracciones que escriban fuera de la salida.
- [x] Decodificar con `apktool d --only-manifest` a un directorio nuevo; comprobar XML legible y valores `com.pixel.gun3d`, `1191`, `11.3.1`, mínimo 15 y objetivo 24. Apktool normaliza versión/SDK en `apktool.yml`; recursos completos no certificados y diez avisos conservados.
- [x] Guardar resultados/logs y hashes de muestras. No se recompiló, firmó, instaló ni ejecutó el APK.

**Aceptación:** JADX produce Java interpretable de una clase real y Apktool recupera correctamente el manifiesto. Los errores de clases individuales se registran, no se silencian.

## Tarea 5 — SDK y dispositivo aislado

**Archivos:** actualizar lock/matriz y `./docs/lab/dispositivo-laboratorio.md`; datos privados bajo `./.lab/private/device/`.

**Consume:** host, autorización de cambios y elección de dispositivo. **Produce:** `RUNTIME_READY` o bloqueo específico; no condiciona `STATIC_READY`.

- [x] Instalar Platform-Tools en ruta local y comprobar `adb version`. Instalados ADB 37.0.1 y Command-line Tools 17.0 build 12700392, con licencia autorizada exclusivamente para SDK/ADB. Emulador/imagen no instalados; Build-Tools diferidos. No se inició el servidor ADB ni se consultaron dispositivos.
- [x] Elegir **AVD x86 de laboratorio** como candidato inicial por el host x86_64; alternativa: dispositivo dedicado ARMv7. Selección documentada, **sin crear ni arrancar AVD**, ni usar teléfono personal.
- [x] Consultar metadata oficial de imágenes y fijar candidato: API 25, Android 7.1, default x86, revisión 1; emulador 37.2.12 estable. No se descargaron y su compatibilidad efectiva sigue sin probarse.
- [ ] Si se usa AVD, pedir autorización para resolver acceso al grupo KVM, renovar sesión y comprobar `emulator -accel-check`. No usar `chmod 666 /dev/kvm` ni ejecutar el emulador como root.
- [ ] Configurar un único AVD, inicialmente 2 GiB de RAM y 2 vCPU; no ejecutar extractores pesados simultáneamente. Comprobar espacio real para sistema, snapshots y OBB.
- [ ] Arrancar Android sin el APK. Registrar `adb devices -l`, API, `ro.product.cpu.abilist`, `ro.product.cpu.abilist32` y, si esas propiedades faltan, `ro.product.cpu.abi`/`abi2`. Exigir `x86` o `armeabi-v7a` utilizable, no inferirlo de la CPU del host.
- [ ] Establecer denegación de salida en el límite del laboratorio mediante mecanismo aprobado —red aislada/namespace/firewall del proceso o segmento dedicado— preservando ADB. No cambiar indiscriminadamente el firewall global.
- [ ] Probar que Android no puede alcanzar un destino externo controlado, y que ADB sigue operativo. Registrar regla y verificación; modo avión por sí solo no prueba el aislamiento de un emulador.
- [ ] Crear snapshot limpio o procedimiento equivalente de restauración del dispositivo dedicado. No cargar cuentas reales, compras ni credenciales de producción.

**Aceptación:** dispositivo visible por ADB, ABI compatible, almacenamiento suficiente, aislamiento comprobado y restauración documentada. La ejecución efectiva del juego se prueba en el plan 2; no se afirma que vaya a arrancar solo porque Android arranque.

## Tarea 6 — Cierre y entrega

**Archivos:** finalizar `./.lab/toolchain.lock.json` y `./docs/lab/estado-herramientas.md`.

**Consume:** evidencias de tareas 1–5. **Produce:** capacidades utilizables por el plan 2.

- [x] Repetir comprobaciones esenciales desde un shell limpio cargando únicamente `./.lab/env.sh`; confirmar rutas reales y versiones, no comandos homónimos del sistema. SDK/ADB también comprobados tras su instalación autorizada.
- [x] Revisar logs y distinguir fallos de instalación, incompatibilidad, muestras incompletas y bloqueos administrativos.
- [x] Evaluar `STATIC_READY`: **DEFERRED**, con cuatro de cinco herramientas funcionales PASS y UnityPy PARTIAL. Enumerar capacidades utilizables sin habilitar tareas dependientes de la lectura fallida.
- [x] Evaluar `RUNTIME_READY`: **BLOCKED**, sin dispositivo/ABI/aislamiento/restauración comprobados; no bloquea todo el análisis estático.
- [x] Registrar espacio libre final y confirmar ausencia de emuladores/servidores web innecesarios al cierre. Última medida tras SDK/ADB: 216,67 GiB libres; no se inició servidor ADB.
- [x] Mantener Ghidra, Frida, captura avanzada, dnSpyEx y herramientas de firma como `DEFERRED`; instalarlas requerirá una pregunta técnica y una prueba de aceptación concreta.
- [x] Entregar matriz con `herramienta | versión | prueba | resultado | log | bloqueo`, sin claves ni identificadores personales.

## Fuentes y verificación de comandos

- ILSpyCmd, instalación y opciones `-l`, `-t`, `-r`: https://www.nuget.org/packages/ilspycmd
- UnityPy: https://github.com/K0lb3/UnityPy
- AssetRipper: https://github.com/AssetRipper/AssetRipper
- JADX: https://github.com/skylot/jadx
- Apktool: https://apktool.org/docs/cli-parameters/
- Android SDK: https://developer.android.com/tools
- ADB: https://developer.android.com/tools/adb
- Aceleración/KVM: https://developer.android.com/studio/run/emulator-acceleration

Las opciones necesarias se contrastaron con documentación oficial y ayuda CLI cuando hizo falta. La captura de ayuda ILSpy se omitió al reducir comprobaciones. El avance y las limitaciones de la instalación ejecutada constan en la tabla inicial y en `./docs/lab/`; no se infiere ejecución del juego ni disponibilidad integral de recursos o runtime a partir de versiones.
