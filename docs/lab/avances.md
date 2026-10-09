# Avances del laboratorio

Actualizado: **2026-10-09**. Referencia: [plan 1 de instalación y verificación](../superpowers/plans/2026-10-09-01-instalacion-verificacion-herramientas.md).

## Estado actual — continuación autorizada del Plan 2

**Runtime offline comprobado en `20261009T213202Z`:** Emulator 37.2.12.0 e imagen AOSP Android7.1.1/API25/default/x86 r1 instalados/verificados; dos sesiones del APK/OBB originales alcanzaron el tutorial y la segunda comprobó cámara/avance del aviso. Namespace bubblewrap sin salida, ADB continuo, cero cuentas y restauración fría verificados. **Sin tocar firewall, grupos/KVM, originales ni perfiles.** KVM sigue inaccesible; TCG observado es lento/no soportado, válido solo para la prueba acotada. Sin commits/delegación.

El análisis estático anterior procesó cuatro ensamblados y el staging; piloto de recursos sigue PARTIAL. [Conclusiones actuales](../analysis/conclusiones-y-bloqueos.md), [ejecución y límites](../analysis/ejecucion-controlada.md), [preparación y reversión](preparacion-runtime.md).

No hace falta nueva autorización ni acción administrativa para el mecanismo ya comprobado. **Firewall sigue excluido hasta propuesta/rollback aprobados**; cualquier experimento online es una decisión separada. Menú principal, movimiento/disparo y lectura OBB trazada no certificados.

## Historial del Plan 1 — resumen

**Las secciones siguientes conservan el estado anterior a Plan 2.** Sus permisos/instalaciones pendientes y afirmaciones de no arranque corresponden a ese historial, no al estado actual descrito arriba.

Instalación local de herramientas realizada bajo `.lab/`, con versiones y procedencia fijadas en `.lab/toolchain.lock.json`. Se ejecutaron subagentes con thinking **high**, no xhigh. Por indicación del usuario se priorizó la instalación y se cancelaron revisiones por tarea y suites adicionales; se conservaron comprobaciones mínimas de integridad, versiones y muestras reales.

| Herramienta | Versión instalada | Avance comprobado |
|---|---|---|
| .NET SDK / runtime | 10.0.401 / 10.0.12 | Instalación local y ejecución de ILSpyCmd |
| ILSpyCmd | 11.1.0.9782 | Tres clases listadas; WeaponManager decompilada con 27 DLL originales como referencias y 108 cuerpos de métodos |
| UnityPy | 1.25.4, venv Python 3.14.4 | Instalado; reconoce Unity 5.3.7p1 y enumera 18 objetos, pero la lectura de PlayerSettings es parcial |
| AssetRipper Free | 2.0.0 | Importa/procesa muestra con Managed, detecta Mono/5.3.7p1; UI solo loopback y cerrada |
| Eclipse Temurin JDK | 21.0.12.1+1-LTS | JAVA_HOME local; ejecuta JADX y Apktool |
| JADX | 1.5.6 | Decompila una clase bootstrap real del DEX, con métodos y referencias Android |
| Apktool | 3.0.3 | Recupera manifiesto legible y los cinco valores de paquete, versión y SDK de la muestra |
| Android Command-line Tools | 17.0, build 12700392 | `sdkmanager --version` y propiedades locales comprobados |
| Platform-Tools / ADB | 37.0.1, build 15733141 | `adb version` comprobado; sin iniciar servidor ni consultar dispositivos |

El Python del sistema no se sustituyó. UnityPy y sus dependencias quedaron en `.lab/venvs/unitypy`; el resto de nuevas distribuciones está bajo `.lab/tools/`. No se instalaron paquetes del sistema ni se modificó `~/.bashrc`.

## Capacidades y límites

| Capacidad | Estado | Alcance real |
|---|---|---|
| `ILSPY_READY` | PASS | Listado y decompilación de la muestra Managed; no todos los ensamblados |
| `ASSET_TOOLS_READY` | PARTIAL | AssetRipper funciona en la muestra; UnityPy falla al leer PlayerSettings |
| `ANDROID_STATIC_READY` | PASS acotado | Una clase bootstrap y manifiesto/metadata; no gameplay ni recursos completos |
| SDK/ADB | CLI_READY | Herramientas instaladas y CLI comprobada; conexión, dispositivo y ABI pendientes |
| `STATIC_READY` | DEFERRED | No se cumplen las cinco pruebas funcionales completas por el resultado parcial de UnityPy |
| `RUNTIME_READY` | BLOCKED | No hay dispositivo/ABI/aislamiento/restauración comprobados |

Limitaciones conservadas:

- **UnityPy:** `PlayerSettings.read()` falla con `EOFError: read_str out of bounds`. No se diagnosticó ni corrigió aquí; la instalación correcta no certifica la decodificación.
- **AssetRipper:** referencias ausentes de la muestra registradas, sin considerarlas corrupción ni certificar el OBB completo. Listener cerrado; código final de salida de la UI no observado.
- **JADX:** se autorizó `com.prime31.UnityPlayerNativeActivity` en lugar de `com.pixel.gun3d`, cuyo contenido en este DEX es scaffolding. La muestra valida decompilación Android, no gameplay.
- **Apktool:** decode limitado a manifiesto; versión y SDK normalizados en `apktool.yml`. Diez avisos de recursos omitidos conservados, sin afirmar decodificación íntegra.
- **SDK:** `sdkmanager --list_installed` enumera Platform-Tools, pero omite Command-line Tools extraído manualmente sin `package.xml`. Su versión se verificó con CLI y `source.properties`; no se fabricó metadata.

## Autorización de licencia y límites administrativos

El usuario autorizó aceptar **únicamente `android-sdk-license` para instalar SDK/ADB**. Se utilizó el flujo `sdkmanager --licenses`; siete acuerdos distintos se rechazaron. La aceptación y los intentos fallidos/corregidos quedaron en logs privados. Se fijó Command-line Tools 17.0 estable, sin introducir la nueva CLI de 23.0.

Esa autorización **no** concede instalación de emulador o imagen, privilegios, cambios de grupos KVM, modificaciones de red ni ejecución del APK. No se arrancó Android, no se instaló/ejecutó el juego y no se abrió/exportó el OBB completo.

## Uso del entorno

Desde la raíz del proyecto, en Bash:

```bash
source .lab/env.sh
ilspycmd --version
jadx --version
java -jar "$LAB_APKTOOL_JAR" --version
sdkmanager --version
adb version
```

La carga es explícita y no inicia servicios. UnityPy se utiliza mediante `$LAB_UNITYPY_PYTHON` y AssetRipper mediante `$LAB_ASSETRIPPER`.

## Pendientes para continuar

1. Investigar la lectura parcial de PlayerSettings antes de depender del piloto UnityPy del plan 2.
2. Obtener autorización separada para instalar el emulador y la imagen candidata: emulador 37.2.12, Android API 25/default x86, revisión 1. Son selección fijada, no componentes instalados ni compatibles ya demostrados.
3. Autorizar y resolver acceso KVM, sin root para el emulador ni permisos globales indiscriminados.
4. Aprobar un mecanismo de aislamiento de salida que preserve ADB; no se ha cambiado el firewall ni la red del host.
5. Comprobar después dispositivo visible, ABI de 32 bits utilizable, almacenamiento y restauración limpia. Solo entonces evaluar `RUNTIME_READY`; la ejecución del juego corresponde al plan 2, todavía no ejecutado.

Ghidra, Frida, captura avanzada, dnSpyEx, Build-Tools y firma siguen diferidos, sin instalación automática.

## Evidencias y documentación

- [Matriz de herramientas, pruebas, logs y bloqueos](estado-herramientas.md).
- [Perfil y pendientes del dispositivo de laboratorio](dispositivo-laboratorio.md).
- `.lab/toolchain.lock.json`: versiones, URLs fijas, hashes locales y checksums publicados diferenciados. Las comparaciones de integridad realizadas no implican firmas NuGet/Temurin verificadas.
- `.lab/private/logs/task-2/`, `task-3/`, `task-4/`, `task-5-sdk/` y `task-6/`: comandos, stdout/stderr y códigos de retorno.
- `.lab/smoke/{ilspy,assets,android}/validation.json`: resultados de las muestras.
- `.lab/private/sdd/2026-10-09-01-instalacion-verificacion-herramientas/`: historial privado de ejecución, decisiones y comprobaciones del controlador.

Última medida registrada tras SDK/ADB: **216,67 GiB libres**, por encima del margen de 10 GiB. Los logs, binarios y código decompilado permanecen privados; este resumen no incluye credenciales ni identificadores personales. No se inicializó Git ni se crearon commits. Esta actualización documental no ejecutó nuevas instalaciones ni pruebas de herramientas.
