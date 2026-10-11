# Preparación Android autorizada — sin tocar el firewall

Continuación de la tarea 6 del [Plan 2](../superpowers/plans/2026-10-09-02-analisis-ejecucion-controlada.md), autorizada por el usuario el 2026-10-09: instalar lo necesario y preparar autónomamente el laboratorio. **El firewall no está autorizado**: requiere una propuesta concreta y un plan de deshacer cambios antes de cualquier modificación.

Corrida nueva: `20261009T213202Z`. Evidencias privadas en `./.lab/runs/20261009T213202Z/`. La corrida estática `20261009T191951Z` conserva sus resultados originales.

**Resultado comprobado:** emulador/imagen instalados, Android 7.1.1/API25/x86 arrancado, aislamiento/restauración verificados y dos sesiones originales alcanzaron el tutorial. La segunda validó cámara y avance del aviso del tutorial. [Evidencia y límites](../analysis/ejecucion-controlada.md). KVM sigue inaccesible, pero TCG fue viable para este diagnóstico; no es una afirmación de soporte/rendimiento normal.

## Alcance mínimo

- Copiar Command-line Tools 17.0 y Platform-Tools 37.0.1 ya verificados al SDK local de este worktree. Reutilizar el JDK original solo lectura; no modificar el checkout vecino.
- Instalar desde las URLs exactas del lock Android Emulator 37.2.12 y AOSP API 25/default/x86 revisión 1, verificando tamaño y SHA1 publicado por Google; guardar SHA256 local separado.
- Mantener entradas APK/OBB/unpacked inmutables y todos los nuevos logs/AVD/cachés privados. No instalar Android Studio, Unity Editor, herramientas de firma ni herramientas opcionales sin necesidad.
- El acuerdo `android-sdk-license` ya aceptado se aplica a estos dos paquetes; la autorización actual amplía el alcance de instalación. No fabricar archivos de aceptación ni aceptar otros acuerdos.
- No modificar grupos, permisos de `/dev/kvm`, sysctl, AppArmor, perfiles del usuario, servicios, rutas del host, puentes ni firewall. La autorización permite preparar lo demás, pero no hay privilegio administrativo no interactivo disponible.

## Lista operativa y puertas

- [x] Verificar metadata oficial actual, copias/instalación exclusivas y versiones CLI; dejar registros de comandos, rc y checksums.
- [x] Comprobar aislamiento alternativo: bubblewrap 0.11.1 `--unshare-net` crea un namespace distinto, con solo loopback y sin rutas externas; prueba inicial PASS. No crea veth, NAT, puente ni reglas de firewall.
- [x] Crear un AVD dedicado, sin cuentas, API 25/x86 de 32 bits; no conectar dispositivos personales. ADB y emulador vivirán juntos dentro del namespace aislado.
- [x] Comprobar boot, ABI, almacenamiento, ausencia de cuentas y denegación real de un destino externo controlado; conservar evidencia de que ADB sigue funcionando. La mera desconexión de Wi-Fi no basta.
- [x] Comprobar restauración a un estado limpio. No arrancar el APK mientras alguna puerta esté sin verificar.
- [x] Si el entorno resulta viable, ejecutar como máximo dos pruebas iniciales de los APK/OBB originales siguiendo el guion de Plan 2, con logcat completo, hashes, capturas y cierre; un tercero solo por hipótesis explícita.
- [x] Registrar incidencias y límites: metadata manual del emulador rechazada por avdmanager (instalación oficial SDKmanager resuelta); locks de PID reutilizado retirados solo del AVD propio tras comprobar cierre. No se parcheó el juego ni habilitó Internet.

### KVM y alternativa acotada

`/dev/kvm` existe, pero esta sesión no pertenece a su grupo y no tiene acceso de lectura/escritura. `sudo -n true` requiere autenticación interactiva. No pedir ni almacenar contraseñas, ni usar Docker/LXD para eludir esta barrera.

Se realizó un boot acotado sin aceleración (`-accel off`, `ANDROID_I_WANT_MY_TCG=yes`) dentro del namespace. La documentación oficial advierte que TCG es lento y no soportado: **no se considerará viable hasta observar un arranque real**. Un vCPU y renderer software limitan consumo; ventana de boot inicial máxima 8 minutos. Si no funciona, presentar el cambio administrativo mínimo de grupo KVM y su reversión, para que el propietario lo ejecute localmente; no cambiar `chmod` a permisos públicos.

## Reversión sin firewall

1. Detener el juego y el emulador, matar el servidor ADB dedicado y salir de bubblewrap. Al terminar sus procesos, el namespace temporal desaparece; comprobar procesos/listeners restantes y que el namespace/rutas del host no han cambiado.
2. Restaurar o descartar **solo** el AVD de esta corrida. Conservar logs privados de diagnóstico; no borrar evidencia anterior ni instalaciones ajenas.
3. Si se desea retirar la instalación, borrar exclusivamente las nuevas carpetas de emulador e imagen indicadas por el recibo, y las copias SDK locales creadas por esta continuación. Antes cotejar identidad y que ningún proceso las usa. No ejecutar limpieza global de Git ni SDK.
4. Al no haber modificaciones de firewall, grupos, sysctl o perfiles, no hay cambios persistentes de esos tipos que revertir. Si posteriormente fueran necesarios, preparar primero otro plan con estado previo, comandos exactos, verificación de ADB y rollback; **no ejecutarlo sin aprobación**.

## Referencias

- [Comandos y TCG](https://developer.android.com/studio/run/emulator-commandline)
- [Aceleración/KVM y renderer](https://developer.android.com/studio/run/emulator-acceleration)
- [avdmanager](https://developer.android.com/tools/avdmanager)
- [bubblewrap](https://github.com/containers/bubblewrap): ayuda local y prueba real conservadas en la corrida.
- Metadata de Google descargada en `RUN/docs/{sdk-repository,image-repository}.xml`; URLs/hashes esperados en `./.lab/toolchain.lock.json`. Consulta Context7 completada sin credenciales; no instalar versiones flotantes del runtime.
