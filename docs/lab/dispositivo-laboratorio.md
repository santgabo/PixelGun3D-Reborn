# Perfil de dispositivo de laboratorio — BLOCKED

Fecha: 2026-10-09. **SDK/ADB instalados; ningún dispositivo configurado ni arrancado.** No se instaló ni ejecutó el APK. Se aceptó únicamente `android-sdk-license` por autorización directa «si» del usuario para Command-line Tools y Platform-Tools; no se cambiaron KVM, red o host.

Resumen general: [avances del laboratorio](avances.md). Pruebas y capacidades estáticas: [estado de herramientas](estado-herramientas.md).

## Componentes fijados

| Componente | Versión / perfil | Estado |
|---|---|---|
| Platform-Tools / ADB | 37.0.1 Linux, build 15733141; protocolo 1.0.41 | INSTALADO / CLI_READY: `adb version` rc0; sin servidor ni consulta de dispositivos |
| Command-line Tools | 17.0, build 12700392 | CLI_READY: `sdkmanager --version` rc0 con JDK 21 local |
| Android Emulator | 37.2.12 Linux x64 | BLOCKED: instalación no autorizada; KVM/aislamiento pendientes |
| Imagen candidata | API 25, Android 7.1, default x86, revisión 1 | BLOCKED: instalación no autorizada; arranque/ABI no probados |
| AVD previsto | Un AVD, 2 GiB RAM, 2 vCPU | No creado; no inferir ABI del host |

SDK instalado exclusivamente en `.lab/tools/android-sdk/{cmdline-tools/17.0,platform-tools}`; PATH opt-in mediante `source .lab/env.sh`, caches/datos Android bajo `.lab/private/`. Descargas desde URLs exactas del lock, SHA1 publicados Google coincidentes y SHA256 locales separados. ZIP inspeccionados y extraídos sin sobrescribir instalaciones previas. Rutas reales, versiones y `source.properties` comprobados desde shell limpio; los checks CLI no prueban conexión ni ABI.

`sdkmanager --list_installed` rc0 registra Platform-Tools 37.0.1, pero **no enumera Command-line Tools del ZIP manual** (sin `package.xml`); su 17.0 está verificado por CLI y `source.properties`, sin fabricar metadata ni reinstalar. La licencia la escribió el flujo documentado `sdkmanager --licenses`: respuesta positiva solo a `android-sdk-license`; todos los demás acuerdos fueron rechazados. Texto, hash y transcript privados en `.lab/private/logs/task-5-sdk/`. Aunque otros paquetes usen la misma licencia técnica, esta autorización **no permite instalar emulador o imagen**.

Alternativa solo si el AVD resulta incompatible: dispositivo dedicado con ARMv7, nunca teléfono personal con cuentas o datos.

## Puertas y siguientes autorizaciones

1. SDK/ADB: autorización concedida y licencia aceptada; ya no bloquean su instalación. **Emulador e imagen siguen sin autorización de instalación**, sin Build-Tools, system images ni AVD añadidos.
2. Autorizar acceso administrativo de lectura/escritura a `/dev/kvm` y renovación de sesión. El preflight previo registró falta de acceso; no se repitió ni se alteraron grupos/permisos. Después comprobar aceleración, sin root ni `chmod 666`.
3. Aprobar mecanismo de denegación de salida en el límite del laboratorio que preserve ADB. No cambiar firewall global; verificar denegación hacia destino externo controlado y continuidad de ADB antes de ejecutar APK.
4. Tras las autorizaciones pertinentes, arrancar solo Android, comprobar dispositivo visible, API, ABI de 32 bits `x86` o `armeabi-v7a`, almacenamiento suficiente y restauración limpia. No usar cuentas, compras ni credenciales reales. La RAM del host está por debajo de los 16 GB recomendados para emulador; rendimiento no probado.

**RUNTIME_READY=BLOCKED**: sin dispositivo visible, ABI efectiva, aislamiento ni restauración comprobados. Disco libre tras SDK/ADB: 232650715136 bytes (216,67 GiB; mínimo local 10 GiB), pero almacenamiento del guest no probado. Esta puerta es independiente de `STATIC_READY=DEFERRED` y UnityPy PARTIAL; tampoco Android arrancado probaría que el juego funciona.

Evidencia SDK/ADB: `.lab/private/logs/task-5-sdk/`; confirmación posterior de versiones por el controlador: `.lab/private/sdd/2026-10-09-01-instalacion-verificacion-herramientas/controller-sdk-adb-versions.log`; cierre histórico previo: `.lab/private/logs/task-6/`. No se ejecutaron `adb devices`, `adb start-server`, emulador ni APK. Ghidra, Frida, captura avanzada, dnSpyEx, Build-Tools/apksigner y herramientas de firma continúan DEFERRED; requieren necesidad técnica y aceptación concreta, no instalación automática.
