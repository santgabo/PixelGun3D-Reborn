# Flujo de arranque — análisis estático PARTIAL

Corrida **20261009T191951Z**, APK original **com.pixel.gun3d 11.3.1 / 1191**. Herramientas: Apktool **3.0.3**, JADX **1.5.6**, ILSpyCmd **11.1.0.9782**, UnityPy **1.25.4**. Evidencia privada bajo `./.lab/runs/20261009T191951Z/` (`RUN`).

## Correlación dinámica posterior

Corrida autorizada `20261009T213202Z`: dos referencias originales en API25/x86 con salida denegada alcanzaron el tutorial; la segunda comprobó cámara y paso al aviso de movimiento. Unity/Mono ejecuta lógica y el cliente confirma OBB presente; sus bytes en guest coinciden, pero no se trazó lectura efectiva. Primer menú, orden completo de escenas/SDK y primera operación de red efectiva siguen no probados. [Evidencia dinámica](./ejecucion-controlada.md).

El resto de este documento describe el análisis estático de `20261009T191951Z`; sus afirmaciones de no lanzamiento/no permisos son históricas para esa corrida, no para la continuación.

## Evidencia Android

Apktool decodificó manifiesto, recursos y smali en `android/apktool/`, sin recompilar ni firmar. JADX procesó el APK en `android/jadx/` (sin duplicar recursos), **4.253 archivos Java**. Ambas CLI devolvieron rc0, pero el Java contiene **717 anotaciones diagnósticas en 257 archivos/clases**, inventariadas por archivo/línea en `android/inspection.json`. Los fallos/avisos individuales no quedan certificados por rc0.

Paquete/versión/SDK contrastados con manifiesto + `apktool.yml`: **com.pixel.gun3d**, **1191 / 11.3.1**, mínimo **15**, objetivo **24**. Manifiesto: MAIN + LAUNCHER/LEANBACK_LAUNCHER sobre **com.prime31.UnityPlayerNativeActivity**, singleTask, paisaje. No se lanzó actividad alguna.

## Secuencia sustentada en código

1. **Actividad:** `com.prime31.UnityPlayerNativeActivity.onCreate(Bundle)` llama a `super.onCreate`, después crea `ActivityProxyObjectHelper`. Aunque su nombre contiene “Native”, su superclase en esta copia es **com.unity3d.player.UnityPlayerActivity**, no la clase UnityPlayerNativeActivity homónima del motor. Contraste independiente: `android/apktool/smali/com/prime31/UnityPlayerNativeActivity.smali`, directiva `.super`.
2. **Vista/runtime:** `com.unity3d.player.UnityPlayerActivity.onCreate` construye `UnityPlayer`. `UnityPlayer.<clinit>` intenta `loadLibraryStatic("main")`; su constructor invoca `NativeLoader.load(nativeLibraryDir)`, comprueba disponibilidad, `initJni`, `nativeFile(packageCodePath)` y `j()`. La cadena nativa interna posterior (incluida la carga de Mono) no se reconstruyó aquí.
3. **Expansión:** `UnityPlayer.a(Context)` obtiene versionCode y examina `Android/obb/<paquete>/main.<versión>.<paquete>.obb` y patch. `j()` registra archivos con `nativeFile` solo cuando `useObb` y la comprobación de configuración correspondiente lo permiten. `staging/Data/settings.xml` declara `useObb=True`; no se publicó su identificador de configuración ni se modificó. Presencia del archivo no garantiza que el runtime llegue a leerlo.
4. **Puente administrado:** `Assembly-CSharp-firstpass::GooglePlayDownloader.GetExpansionFilePath/GetMainOBBPath/FetchOBB` utiliza Environment, el paquete/versión y UnityDownloaderActivity. `UnityDownloaderService` proporciona la integración de downloader; no se intentó descargar recursos ni validar servicios/licencias en línea.
5. **Escenas/scripts:** `globalgamemanagers` **path_id 11**, BuildSettings, lista 109 escenas; índice 0 **Assets/Scenes/AppCenter.unity**, índice 1 **Assets/Loading.unity**. `level0` **path_id 16** referencia `globalgamemanagers.assets` **path_id 1437**, `Assembly-CSharp.dll::AppsMenu`; **path_id 17** referencia **278**, `Rilisoft.SceneLoader`. Esos dos enlaces se verificaron solo a nivel de cabecera; sus campos personalizados no están resueltos.
6. **AppsMenu:** `Awake` inicializa registros/estado e indicador; `Start` ejecuta su coroutine de preparación, valida condiciones de plataforma y, si el build está dividido, comprueba OBB/permisos. Con expansión ausente puede esperar permiso de almacenamiento y llamar a `GooglePlayDownloader.FetchOBB`. `Fade` llama a `LoadLoading`, que solicita `SceneManager.LoadSceneAsync("Loading")`. Esta es una ruta de código, **no un hito observado**. La clase `Launcher` existe, pero no se sustituyó por la evidencia de AppCenter ni se asumió activa en el arranque de esta copia.
7. **Mensajes/JNI:** `UnityPlayer.UnitySendMessage` llama a `nativeUnitySendMessage`; `com.prime31.EtceteraPluginBase.UnitySendMessage` invoca ese puente por reflexión. En C# se encuentran AndroidJavaClass/AndroidJavaObject y coroutines. No se instrumentaron esos puntos.

## Permisos y ABI

Se registran INTERNET/ACCESS_NETWORK_STATE, almacenamiento externo y ubicación, entre otros, desde el manifiesto; servicios de notificación, anuncios y compras están presentes. **No se concedió ningún permiso**, no se usaron cuentas ni se asumió que un SDK presente bloquea el arranque.

Las bibliotecas originales son ELF de **32 bits ARMv7 y x86**. ARM incluye `libAmazonGamesJni.so` y `libImmEndpointWarpJ.so` ausentes de x86. La misma versión de Android con ABI diferente no garantiza comportamiento equivalente; listado/cabeceras en `android/native-libraries.json`. No se infirió compatibilidad del host x86_64 ni de ADB.

## Hechos, inferencias y huecos

- **Confirmado estáticamente:** actividad, paquete/versión, búsqueda de OBB, JNI/UnitySendMessage, lista BuildSettings y referencias de cabecera a AppsMenu/SceneLoader.
- **Inferido:** AppCenter como primera escena esperada y transición a Loading si se satisfacen sus condiciones. Falta observación dinámica de ambas.
- **No probado en el análisis estático:** primer menú, primera operación de red efectiva, lectura OBB, inicio Unity/Mono y función local. La continuación posterior confirma inicio/tutorial/cámara; menú/red efectiva/lectura trazada siguen pendientes. `PhotonNetwork.ConnectUsingSettings` demuestra rutas posibles de red, **no su orden ni ejecución efectiva**. No se extrapola la presencia de SDK al orden de sus llamadas.

## Guion dinámico condicionado

Solo tras **RUNTIME_READY=PASS** y autorización de entorno: restaurar estado limpio sin cuentas; fijar serial de laboratorio; instalar el APK original sin reemplazar una instalación previa; copiar el OBB original exacto; verificar tamaño/hash en guest. Capturar logcat completo y momento UTC; lanzar el componente confirmado con `am start -W -n`; observar proceso, runtime, expansión y escena por separado.

Observar 120 s, ampliar hasta 5 min únicamente si hay progreso; capturas en cada hito. Navegación básica y opción local únicamente si existe: sin login/compras, sin abrir Internet para resolver un bloqueo. Repetir una vez desde el mismo estado limpio; un tercer intento solo con hipótesis de entorno explícita. Finalizar juego/captura y restaurar estado, verificando procesos/listeners. Procedimiento y puerta actual: [ejecución controlada](./ejecucion-controlada.md).
