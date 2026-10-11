# Ejecución controlada — tutorial completo y menú verificados

**Actualización 2026-10-11:** nueva [ejecución original con KVM](./continuacion-plan-2-2026-10-11.md), APK/OBB autenticados y namespace offline. Dos instalaciones limpias completaron cámara, movimiento, salto, recogida de arma, disparo, recarga, tutorial y llegada al menú. Farm cargó offline con movimiento, disparo y retorno al menú en un perfil de progreso antiguo derivado separado; las corridas están cerradas. También se observó un descriptor OBB con posición dentro del payload de un miembro ZIP. Adventure exige onboarding multijugador desde una instalación limpia; el fallo de migración y una terminación externa del laboratorio se conservan en el informe. Las dos referencias siguientes son históricas del 2026-10-09.

Corrida dinámica **20261009T213202Z**, 2026-10-09 UTC. **Dos ejecuciones del APK/OBB originales alcanzaron el tutorial; la segunda comprobó rotación de cámara y avance del tutorial.** No se modificó el juego ni se habilitó Internet. Esto no certifica el menú principal, el multijugador ni todo el gameplay.

La corrida estática anterior **20261009T191951Z** quedó bloqueada antes del lanzamiento. Su `runtime/readiness.json` y resultados se conservan como evidencia histórica, no como estado actual.

Evidencias privadas: `./.lab/runs/20261009T213202Z/` (`RUN`). Resumen: `RUN/reports/runtime-results.json`. Preparación/reversión: [preparación Android](../lab/preparacion-runtime.md). Perfil: [dispositivo](../lab/dispositivo-laboratorio.md).

## Autorización y entorno

El usuario autorizó instalaciones necesarias y preparación autónoma; **excluyó el firewall hasta recibir propuesta y rollback**. Se instaló únicamente lo necesario y se usó una alternativa que no toca el firewall. No se cambiaron grupos, permisos KVM, sysctl, AppArmor, servicios ni perfiles del usuario.

| Elemento | Perfil comprobado |
|---|---|
| Android Emulator | 37.2.12.0, build 16428233; paquete exacto del lock |
| Android | AOSP 7.1.1 / API 25, default x86, revisión 1; ABI efectiva `x86` de 32 bits |
| SDK/ADB | Command-line Tools 17.0 y Platform-Tools 37.0.1; servidor ADB exclusivo dentro del namespace |
| AVD | Nexus S, 480×800; aplicación en paisaje 800×480; 2 GiB RAM, un vCPU |
| Renderer | `-gpu software`, SWANGLE/lavapipe observado; audio deshabilitado |
| Aceleración | KVM inaccesible; TCG con `-accel off` y `ANDROID_I_WANT_MY_TCG=yes` |
| Almacenamiento | Aproximadamente 6 GiB libres al comenzar; partición efectiva mayor que los 4 GiB solicitados |
| Cuentas | `dumpsys account`: **Accounts: 0** antes de cada instalación |
| Aislamiento | bubblewrap 0.11.1; namespace de red separado, solo loopback, sin rutas externas |
| Restauración | Copia fría del AVD limpio; hashes de 12 archivos y ausencia de dos marcadores de prueba verificadas |

**TCG es lento y oficialmente no soportado**. El primer boot observado completó en 65,2 s; los dos ensayos posteriores demostraron que es viable para este diagnóstico acotado, no para afirmar rendimiento normal. No hizo falta acceder a `sudo` ni sortear su autenticación.

El namespace también oculta el home del host y sus sockets de servicios; SDK/JDK y entradas del experimento se montan solo lectura. ADB/emulador viven juntos en su loopback aislado. En cada sesión se comprobó TCP externo `ENETUNREACH`, ping guest `Destination Host Unreachable` y continuidad de ADB después de la denegación. No se creó puente, NAT ni regla de firewall.

## Entradas y procedimiento

- APK original: **32.357.906 bytes**, copia privada de la extracción verificada anterior; sin parchear, recompilar ni firmar.
- OBB original: **435.792.640 bytes**, copiado con nombre exacto a `/sdcard/Android/obb/com.pixel.gun3d/main.1191.com.pixel.gun3d.obb`.
- Actividad: `com.pixel.gun3d/com.prime31.UnityPlayerNativeActivity`, confirmada en manifiesto/smali.
- Solo se concedió explícitamente `WRITE_EXTERNAL_STORAGE` dentro del guest descartable: AppsMenu comprueba almacenamiento escribible y el APK apunta a API 24. No se concedieron permisos en bloque ni ubicación.

Se comprobó que el paquete no existía antes de instalar, y se capturó logcat completo antes de la instalación/lanzamiento. `am start -W -n` devolvió rc0 en ambos ensayos. Hubo capturas y PID/estado de ventana a 0, 15, 30, 60 y 120 s. El proceso seguía presente al final y la ventana pertenecía al componente confirmado.

El guest no dispone de `sha256sum`: se recuperó el OBB a una salida privada de **cada ensayo**, y su tamaño/SHA256 coincidieron con el original. Esto verifica los bytes en el dispositivo, no cada lectura posterior del motor.

## Estados observados

| Afirmación | Estado / evidencia |
|---|---|
| Proceso/actividad creados | PASS en ambos; `trial-*/launch-original.*`, `pid-*.stdout`, `window-*.stdout`; logcat de ensayo 2 línea 2718 |
| Unity/Mono ejecutando lógica | PASS; escena 3D interactiva y `Assembly-CSharp::Switcher.Start()`/InitializeSwitcher en logcat (ensayo 1: 2827/2831; ensayo 2: 2856/2860) |
| OBB presente e idéntico | PASS; copias recuperadas/hash; cliente informa `OBB already exists` (ensayo 1: 2773; ensayo 2: 2808) |
| Lectura efectiva del OBB trazada | **NO PROBADA**: inspección `/proc/<pid>/fd` denegada al usuario shell; existencia y tutorial no se convierten en una traza de lectura |
| Primer estado visible estable | PASS: tutorial con arma/escenario y aviso “Swipe around this area to rotate”, en ambos `screen-120.png` |
| Menú principal | NOT_RUN: no se llegó ni se buscó fuera del tutorial |
| Función local | PASS, solo ensayo 2: dos gestos en la zona derecha rotan la vista y cambian el aviso a “Tap and drag to move around”; `camera-swipe*.json`, `screen-after-camera*.png` |
| Movimiento/disparo/completar tutorial | NOT_RUN |
| Inicio reproducible | PASS: mismo estado limpio, mismas entradas/permisos/parámetros; tutorial en ambos ensayos. La interacción de cámara solo se probó en el segundo |
| Servicios externos | No habilitados; error DNS de filtro de palabras en ambos, coherente con aislamiento. No se concluye que el servidor real esté caído |

La correlación dinámica confirma una función local del original. No identifica por sí sola el archivo `levelN` de la escena ni el orden de toda la inicialización de SDK. No hubo compras, login, cuentas personales, instrumentación ni una tercera ejecución del juego.

## Incidencias de preparación resueltas

1. El ZIP manual del emulador tenía CLI válida pero no `package.xml`; avdmanager lo rechazó. SDKmanager realizó la instalación oficial estable y generó su propia metadata. **398 archivos coinciden byte a byte con el ZIP fijado**; solo añadió `package.xml`. El árbol manual se conserva, sin fabricar metadata.
2. El cierre por consola dejó dos locks con PID del namespace, provocando falso “multiple emulators” al reutilizar esos PID. Se comprobó ausencia de procesos, conservaron los locks y excluyeron únicamente esos dos archivos transitorios de la plantilla. La prueba de restauración pasó después.
3. La solicitud de RAM llevó al emulador a elevar automáticamente heap a 512 MiB; no se presenta el 256 MiB solicitado como efectivo.

## Cierre e integridad

Se ejecutó `am force-stop`, terminó logcat y se cerraron emulador/servidor ADB. Códigos observados: emulador **-10** tras `emu kill` (mensaje de cierre por consola conservado), capturas logcat **-15** por SIGTERM. No se los confunde con un crash del juego.

Los AVD usados se preservan privados como evidencia; el AVD activo se restauró a la plantilla limpia, con hashes coincidentes. No quedaron procesos/listeners del laboratorio ni namespace persistente; namespace del host igual al inicial. Rehash final de **10.393 originales / 1.977.291.055 bytes: PASS**, sin cambios/faltantes/extras. Copias redactadas de logcat siguen privadas; no publicar los originales.

**No es necesario un plan de firewall para este mecanismo, porque no lo modifica.** Cualquier experimento posterior de red necesita propuesta separada, verificación y rollback antes de aprobación/ejecución.
