# Perfil de laboratorio — referencia offline comprobada

Actualizado **2026-10-09**. Corrida **20261009T213202Z**. **RUNTIME_READY=PASS acotado** para la referencia observada: dos arranques originales al tutorial y rotación de cámara comprobada en el segundo. No significa compatibilidad completa ni servicios online disponibles.

El usuario autorizó instalaciones/preparación autónoma, excepto firewall sin propuesta y rollback previos. **No se modificó el firewall**, grupos, KVM, sysctl, AppArmor, servicios ni perfiles del usuario. La evidencia histórica del bloqueo está en corrida `20261009T191951Z`; ya no es el estado actual.

## Perfil efectivo

| Componente | Versión / estado |
|---|---|
| Command-line Tools | 17.0 build 12700392, copia local verificada |
| Platform-Tools / ADB | 37.0.1 build 15733141; conexión guest y dos capturas completas verificadas |
| Android Emulator | 37.2.12.0 build 16428233, estable; SHA1 publicado coincidente y SHA256 local separado |
| Imagen | AOSP Android 7.1.1/API 25/default x86/revisión 1; ABI efectiva `x86` de 32 bits |
| AVD dedicado | `pg3d_1191_api25_x86`, Nexus S, 480×800, un vCPU, RAM 2048 MiB |
| Renderer / audio | Software SWANGLE/lavapipe; audio deshabilitado |
| Guest / almacenamiento | Sin cuentas; aproximadamente 6 GiB libres inicialmente, OBB original 435.792.640 bytes |
| Restauración | Copia fría limpia, no Quick Boot; hashes de 12 archivos y ausencia de marcadores guest comprobados |
| Red | Namespace bubblewrap separado, solo loopback/sin rutas externas; ADB dentro del mismo namespace |

SDK local: `.lab/tools/android-sdk/`; JDK del checkout primario **solo lectura**. Nuevos HOME/AVD/cachés/logs privados dentro de `.lab/runs/20261009T213202Z/`. No se usan cuentas ni dispositivos personales. El serial de laboratorio es `emulator-5580`, explícito en comandos ADB.

**KVM sigue inaccesible y `sudo` exige autenticación interactiva.** No se eludió: se utilizó TCG (`ANDROID_I_WANT_MY_TCG=yes`, `-accel off`), oficialmente lento/no soportado. El boot inicial completó en 65,2 s y la referencia acotada funcionó. No se necesita actualmente una intervención administrativa para repetir este ensayo; rendimiento y estabilidad más prolongados no certificados.

## Puertas verificadas antes del APK

- Versiones/tamaño/SHA1 coincidentes con lock y metadata estable de Google; SHA256 local registrado.
- avdmanager creó el AVD tras instalación oficial SDKmanager del emulador; 398 archivos coinciden con el ZIP fijado y solo se añade `package.xml` oficial.
- Boot/API/ABI/storage/Accounts0 comprobados en Android limpio.
- TCP externo desde namespace: `ENETUNREACH`; ping guest: `Destination Host Unreachable`; ADB funciona después de esas pruebas.
- Restauración comprobada creando marcadores en `/data/local/tmp` y `/sdcard`, volviendo a la plantilla y verificando su ausencia antes de instalar.
- Paquete ausente antes de instalar; APK original y OBB íntegros. Solo permiso de almacenamiento requerido, no concesión general.

Detalles/hitos/límites: [ejecución controlada](../analysis/ejecucion-controlada.md). Procedimiento y reversión: [preparación runtime](preparacion-runtime.md). Resultado máquina privado: `RUN/reports/runtime-results.json`.

## Cierre y reproducción

Emulador, app y servidor ADB detenidos; AVD activo restaurado, sin procesos/listeners del laboratorio. Locks transitorios solo se retiran de **este AVD**, tras comprobar que no hay procesos; se conservaron los locks originales de diagnóstico. No borrar locks ni reemplazar AVD ajenos.

El archivo privado `RUN/runtime/env.sh` configura rutas/HOME **solo dentro de un proceso controlado**; **no proporciona aislamiento por sí solo**. No lanzarlo directamente fuera de bubblewrap ni cargarlo en el shell personal habitual. Los comandos exactos del namespace y de cada ensayo están en `RUN/logs/*.json`; las entradas y la plantilla se montan solo lectura.

No hay cambios de firewall que deshacer: al salir todos los procesos, el namespace temporal desaparece. Para retirar herramientas/AVD, seguir el recibo y [reversión](preparacion-runtime.md), sin borrar evidencias anteriores ni entradas. Cualquier cambio futuro de firewall requiere el plan y rollback que el usuario exigió; no está autorizado ahora.

## Historial

- Plan 1: solo SDK/ADB instalados, licencia `android-sdk-license` aceptada por el flujo oficial; emulador/imagen/host/red no autorizados entonces.
- Corrida `20261009T191951Z`: diagnóstico estático y bloqueo previo al lanzamiento, sin Android ni juego ejecutados.
- Corrida actual: permiso nuevo amplía instalación a emulador/imagen, usando el mismo acuerdo ya aceptado; instalación, aislamiento alternativo y dos referencias originales comprobadas. Los estados históricos se conservan, no se sobrescriben retrospectivamente.
