# Pixel Gun 3D 11.3.1: tecnologías y herramientas de ingeniería inversa

## 1. Conclusión ejecutiva

Esta copia es una aplicación Android construida con **Unity 5.3.7p1 y el backend Mono**, no IL2CPP. Conserva ensamblados .NET con metadatos y cuerpos de métodos, por lo que la vía principal es **decompilar las DLL con ILSpy**, no comenzar por desensamblar `libunity.so`.

**No hace falta instalar Unity Editor para analizar código, extraer recursos o ejecutar el APK original en Android compatible.** El APK ya contiene el runtime del motor. Sin embargo, extraer C# y recursos **no convierte el juego en una aplicación independiente de Unity**: reconstruirlo en otro motor exige una adaptación/reimplementación considerable.

Herramientas prioritarias en este entorno Linux:

1. .NET SDK/runtime compatible con la versión elegida de **ILSpyCmd**.
2. **AssetRipper** para explorar y recuperar estructura de recursos; **UnityPy** para inventarios y extracción automatizada.
3. Java y **JADX + Apktool** para la capa Android.
4. Android SDK Platform-Tools y un dispositivo/emulador con soporte real de las ABI de 32 bits incluidas.
5. **Ghidra y Frida** solamente cuando una pregunta concreta requiera análisis nativo o dinámico.

## 2. Alcance y grado de verificación

Se inspeccionaron archivos, cabeceras Unity, XML binario del manifiesto, tablas de clases DEX y metadatos CLI de ensamblados. También se contrastaron herramientas con documentación oficial de sus proyectos.

No se ha ejecutado el juego, decompilado todos los métodos, exportado todos los objetos Unity, probado herramientas contra este conjunto completo ni contactado servicios del juego. La existencia de un SDK en el paquete no demuestra que todas sus funciones se ejecuten.

No se modificaron los binarios de `unpacked` ni los archivos originales. No se incluyen claves o valores de configuración sensibles en este informe.

## 3. Identificación de la aplicación

| Elemento | Resultado | Evidencia local |
|---|---|---|
| Paquete Android | `com.pixel.gun3d` | `./unpacked/apk/AndroidManifest.xml`, decodificado en memoria |
| Versión | `11.3.1`, código `1191` | Atributos `versionName` y `versionCode` del manifiesto |
| Android mínimo / objetivo | API 15 / API 24 | `uses-sdk` del manifiesto; no implica compatibilidad garantizada con cualquier Android posterior |
| Motor | Unity `5.3.7p1` | Cabecera de `globalgamemanagers`, otros archivos serializados y cadena en `libunity.so` |
| Backend | Mono / ensamblados CLI | `libmono.so` y `assets/bin/Data/Managed/*.dll` |
| ABI nativas | ARMv7 y x86, ambas de 32 bits | `lib/armeabi-v7a` y `lib/x86`; cabeceras ELF |
| Lanzador | `com.prime31.UnityPlayerNativeActivity` | Manifiesto |
| Capa Android | Un `classes.dex`, formato DEX 035 | Cabecera del archivo; 9.178 definiciones de clase |
| Gráficos declarados | OpenGL ES 2.0 | `uses-feature`, `glEsVersion=0x00020000` |

No se encontraron `libil2cpp.so` ni `global-metadata.dat` en este árbol. La presencia de DLL con cuerpos de métodos y Mono confirma la ruta de análisis administrado para esta copia.

El APK original está dentro de:

- `./apk+obb-original/Pixel Gun 3D [11.3.1].zip`
- Entrada del ZIP: `Pixel Gun 3D [11.3.1].apk`

La expansión original está en:

- `./apk+obb-original/com.pixel.gun3d/main.1191.com.pixel.gun3d.obb`

## 4. Código y tecnologías identificadas

### 4.1. Lógica administrada

Directorio principal:

`./unpacked/apk/assets/bin/Data/Managed/`

Contiene **27 DLL**. Las principales son:

| Ensamblado | Hallazgo |
|---|---|
| `Assembly-CSharp.dll` | Aproximadamente 5,3 MiB; 3.396 entradas TypeDef y 25.597 MethodDef; 24.015 métodos con RVA no nulo |
| `Assembly-CSharp-firstpass.dll` | 248 TypeDef y 2.155 MethodDef; incluye integraciones y código auxiliar |
| `Assembly-UnityScript.dll` | 19 TypeDef y 67 MethodDef |
| `Assembly-UnityScript-firstpass.dll` | 12 TypeDef y 62 MethodDef |
| `Photon3Unity3D.dll` | Cliente Photon; 84 TypeDef y 737 MethodDef |

Los recuentos incluyen tipos generados por el compilador, interfaces y otras estructuras: no equivalen a ese número de clases escritas a mano. Un RVA no nulo es evidencia de cuerpo de método, no garantía de decompilación perfecta.

Los ensamblados inspeccionados declaran metadatos CLR `v2.0.50727`. Es un entorno Mono/.NET heredado; no debe confundirse con el .NET moderno que ejecutará nuestras herramientas.

Hay código UnityScript compilado a IL. ILSpy puede representarlo como C#; eso no recupera necesariamente los scripts originales en UnityScript. `Boo.Lang.dll` y `UnityScript.Lang.dll` acompañan esa infraestructura; su presencia no prueba que los desarrolladores escribieran gameplay en Boo.

Se conservan nombres útiles, entre ellos:

- `Player_move_c`
- `WeaponManager`, `WeaponSounds`
- `ConnectSceneNGUIController`
- `NetworkStartTable`, `NetworkStartTableNGUIController`
- `PhotonNetwork`, `PhotonView`
- `UIRoot`, `UIPanel`, `UILabel`, `UISprite`

Esto favorece el análisis. No demuestra ausencia total de ofuscación ni descarta protecciones en partes específicas.

### 4.2. Acoplamiento a Unity

En `Assembly-CSharp.dll`, 232 de sus 610 entradas TypeRef pertenecen a espacios `UnityEngine*`. No es una medida porcentual del código dependiente, pero sí evidencia de acoplamiento amplio.

Entre los tipos referenciados aparecen:

- Ciclo de vida/escenas: `MonoBehaviour`, `GameObject`, `Transform`, `SceneManager`.
- Renderizado: `Camera`, `Renderer`, `Material`, `Texture2D`, `GL`.
- Física: `Collider`, `BoxCollider`.
- Audio/animación: `AudioSource`, `AudioClip`, `Animation`, `AnimationClip`.
- Ejecución: `Coroutine`, `WaitForSeconds`, `Time`.
- Persistencia/recursos: `PlayerPrefs`, `Resources`.
- Plataforma/red: `AndroidJavaClass`, `WWW`, `WWWForm`, `NetworkView`.

`UnityEngine.dll` no sustituye al runtime nativo: copiarla a un proyecto .NET no proporciona escena, renderizador, física o scheduler de Unity. Los stubs pueden servir para navegación y pruebas de lógica aislada, no para ejecutar el juego completo.

### 4.3. Middleware y SDK presentes

| Área | Evidencia |
|---|---|
| Multijugador | `Photon3Unity3D.dll`, espacios `ExitGames.Client.Photon`, tipos `PhotonNetwork` y `PhotonView`: integración Photon/PUN heredada |
| Red Unity heredada | Referencias a `NetworkView`, `Network`, `RPCMode`; también existe `UnityEngine.Networking.dll`. Falta determinar qué rutas se usan |
| Interfaz | Tipos característicos de NGUI y `UnityEngine.UI.dll` |
| Efectos/animación | `HOTweenMicro.dll`, `Glow11.dll`, `DecalSystem.Runtime.dll` |
| Localización | `ArabicSupport.dll`, espacio `I2.Loc` |
| Puentes Android | Prime31, `AndroidJavaClass`, Google Play Games y bibliotecas JNI |
| Social | Facebook, Amazon GameCircle |
| Compras | Puentes Google IAB y Amazon IAP |
| Publicidad | Fyber, AdColony, AppLovin, Chartboost, Unity Ads, Facebook Ads, Amazon Ads y componentes Google Ads |
| Analítica/servicios | devtodev, Flurry, AppsFlyer; componentes HockeyApp en el manifiesto |
| Notificaciones | Componentes GCM en el manifiesto |

Las integraciones se identificaron por ensamblados, tipos DEX, manifiesto y nombres de bibliotecas. No se han establecido sus versiones exactas ni su estado operativo actual.

## 5. Recursos: APK + OBB

### Distribución

- `./unpacked/apk`: aproximadamente 92 MiB de ocupación en disco.
- `./unpacked/obb`: aproximadamente 1,4 GiB de ocupación en disco.
- `./unpacked/obb/assets/bin/Data`: 9.757 archivos, 1.416.451.862 bytes de contenido.
- Se encuentran archivos lógicos `level0` en APK y `level1` a `level108` en OBB: **109 archivos de nivel**. No equivalen necesariamente a 109 mapas jugables.
- Hay **7.943 archivos con nombre hexadecimal de 32 caracteres** en el OBB. Todos presentan la cabecera serializada inspeccionada de Unity `5.3.7p1`; el nombre no es evidencia de cifrado ni implica que sean AssetBundles.
- Hay archivos auxiliares `.resource`; deben mantenerse junto a los recursos que los referencian.

### Fragmentos `.splitN`

Se detectaron **176 grupos**, con **766 fragmentos** entre APK y OBB:

- APK: 1 grupo, 13 fragmentos.
- OBB: 175 grupos, 753 fragmentos.
- No se detectaron huecos en las secuencias numéricas de fragmentos.
- En los 175 grupos con cabecera de archivo serializado Unity, la suma de tamaños coincide con el tamaño declarado.
- El grupo restante, `sharedassets94.resource`, comienza con `FSB5`: es un contenedor de audio, no un archivo serializado con aquella cabecera de tamaño. No debe marcarse como corrupto por aplicar el validador equivocado.

**Hay que concatenar por sufijo numérico:** `.split0`, `.split1`, ... `.split10`. El orden lexicográfico coloca `.split10` antes de `.split2` y rompe el contenido.

No hay colisiones de rutas relativas entre los dos directorios `assets/bin/Data` inspeccionados. Se puede preparar una vista conjunta en un directorio derivado, conservando estructura, nombres y procedencia. No conviene renombrar arbitrariamente los archivos hexadecimales.

Estas comprobaciones no validan la integridad de todos los objetos, referencias o datos de audio/textura.

## 6. Herramientas recomendadas

### Prioridad 1: código administrado

**ILSpy / ILSpyCmd** — herramienta principal.

- Decompilar `Assembly-CSharp.dll` y los tres ensamblados de scripts restantes.
- Resolver referencias contra la carpeta `Managed` completa de esta misma versión.
- Investigar clases, llamadas, referencias y flujos.
- Exportar C# para lectura; no asumir que el proyecto exportado compilará sin intervención.
- Usar ILSpyCmd en Linux para un proceso repetible.

Requiere .NET compatible con la distribución elegida. Fijar versiones de herramientas: los requisitos del repositorio de desarrollo pueden ser distintos de los de una versión publicada.

**dnSpyEx** — opcional, principalmente para un puesto Windows.

- Útil para inspeccionar/editar IL y ensamblados.
- No es requisito para decompilar en Linux.
- Su soporte de depuración Unity no implica conexión inmediata a este APK Android de producción. Requiere investigar runtime, plataforma y configuración; el proyecto remite a componentes adicionales para Unity.

### Prioridad 1: recursos

**AssetRipper** — exploración y recuperación de estructura Unity.

- Su rango documentado incluye Unity 5.3.
- Puede analizar archivos serializados y exportar recursos a formatos de proyecto Unity.
- Importar recursos y DLL conjuntamente ayuda a resolver scripts/MonoBehaviours.
- No necesita Unity Editor para hacer el análisis/exportación.
- El soporte declarado no garantiza una reconstrucción fiel de este juego; probar primero una muestra pequeña y revisar referencias y logs.
- Un proyecto exportado sigue siendo un proyecto orientado a Unity, no una conversión automática a otro motor.

**UnityPy** — automatización complementaria.

- Inventario por tipos, extracción de TextAssets, texturas, audio, mallas y datos serializados.
- Adecuado para reportes reproducibles en Linux.
- Si faltan type trees de MonoBehaviour, puede requerir generación de tipos desde los ensamblados; su documentación describe `TypeTreeGeneratorAPI` como componente opcional.
- Fijar la versión: el proyecto advierte de cambios incompatibles.

**AssetStudio** — alternativa de consulta/extracción, no primera elección para este entorno Linux.

- El rango documentado 3.4–2022.1 incluye esta versión.
- Útil para inspección visual y exportaciones puntuales, especialmente en un entorno Windows adecuado.
- No es un decompilador de la lógica del juego ni equivale a reconstruir el proyecto.

Para inspección posterior de exportaciones pueden servir un visor/editor 3D y herramientas de audio. No son prerrequisitos para identificar las tecnologías ni reemplazan los extractores Unity.

### Prioridad 1–2: Android

**JADX**

- Decompila `classes.dex` a una representación Java y permite seguir llamadas Android/JNI.
- Priorizar `com.pixel.gun3d`, Prime31, carga del OBB y arranque de Unity.
- No recupera el C# que está en `Managed`.
- El propio proyecto advierte que no decompila siempre el 100 %; recurrir a bytecode/smali para validar casos problemáticos.

**Apktool**

- Decodifica manifiesto binario, recursos y smali.
- Permite reconstruir el empaquetado Android cuando sea necesario.
- No decompila DLL ni recupera escenas Unity.
- `./unpacked/apk` es una extracción del ZIP, no un proyecto Apktool listo para recompilar: todavía contiene manifiesto binario y DEX. Partir del APK original para una decodificación formal.

**Android SDK**

- Platform-Tools: `adb`, instalación y `logcat`.
- Build-Tools, si se modifican copias: `aapt2`, `zipalign`, `apksigner`.
- Una modificación invalida la firma original. Usar una firma de laboratorio cambia identidad criptográfica y puede afectar actualizaciones, login o validaciones de SDK.
- No hace falta Android Studio completo para disponer de las herramientas CLI.

### Prioridad 2–3: ejecución y nativo

**Android compatible, físico o emulado**

- Debe soportar realmente ARMv7 o x86 de 32 bits. No asumir que un dispositivo ARM64 o una imagen x86_64 ejecuta esas ABI.
- La variante ARM tiene bibliotecas adicionales (`libAmazonGamesJni.so`, `libImmEndpointWarpJ.so`) que no aparecen en x86; probar x86 no garantiza comportamiento idéntico.
- Un Android antiguo puede simplificar ciertas compatibilidades, pero debe mantenerse aislado. Versiones actuales pueden introducir restricciones de instalación, almacenamiento o ABI.
- Empezar con una ejecución de referencia del APK original y OBB, en un entorno aislado; después habilitar únicamente las observaciones de red necesarias y autorizadas.

**Frida**

- Instrumentación de Java/JNI y funciones nativas cuando los logs y el análisis estático no basten.
- Requiere preparación del dispositivo: la guía Android describe un dispositivo con root y `frida-server`; también existen alternativas con Gadget.
- Fijar versiones compatibles de cliente/servidor, ABI y Android.
- Inspeccionar Java no expone automáticamente los métodos C# de Mono. La instrumentación de Mono requiere trabajo adicional.

**Ghidra**

- Analizar ELF ARMv7/x86, funciones JNI y bibliotecas nativas concretas.
- `libunity.so` está stripped; su pseudocódigo no recupera el código fuente original del motor.
- Es secundario aquí: empezar por millones de instrucciones del motor sería menos eficiente que leer las DLL de gameplay.

**Captura de red**

- Wireshark/tcpdump pueden complementar un laboratorio autorizado para identificar destinos y protocolos.
- Un proxy HTTP solo sirve para los flujos que realmente sean HTTP(S), con las condiciones TLS correspondientes; no cubre automáticamente Photon ni revela datos cifrados.
- No se ha comprobado si existen certificate pinning, servidores todavía accesibles o dependencias de autenticación obligatorias.

### Herramientas que no priorizaría

- **Il2CppDumper, Il2CppInspector y Cpp2IL**: no corresponden al backend encontrado en esta copia.
- **Desofuscadores automáticos**: no se ha demostrado una protección concreta que los justifique.
- **Unity Editor moderno**: no es necesario para el análisis inicial y no garantiza abrir/reconstruir correctamente un proyecto recuperado de Unity 5.3.
- **Gradle como solución inicial**: reconstruye la envoltura Android en un proyecto preparado, no sustituye Unity ni compila automáticamente el C# heredado.

## 7. Qué podemos hacer sin Unity Editor

| Objetivo | Viabilidad / límite |
|---|---|
| Leer gran parte de la lógica | Alta probabilidad gracias a Mono y metadatos legibles; falta comprobar la decompilación completa |
| Extraer imágenes, audio, mallas y configuraciones | Viable con herramientas externas, sujeto al formato y dependencias de cada objeto |
| Analizar escenas y componentes | Viable parcialmente; exige resolver referencias, scripts y datos serializados |
| Ejecutar el APK original | No requiere Editor; sí Android compatible, recursos y posibles servicios externos |
| Modificar DLL/recursos y reempaquetar una copia | Posible según el cambio; sigue utilizando el runtime Unity incluido y requiere validar firma, serialización y compatibilidad |
| Reconstruir el proyecto original exacto | No garantizado: faltan fuentes originales, metadatos de autoría, ajustes de importación y posiblemente información de shaders |
| Ejecutar el C# decompilado como programa .NET normal | No directamente; depende del runtime y del modelo de objetos Unity |
| Migrar a otro motor | Proyecto de portado/reimplementación, no decompilación automática |
| Recuperar un backend de producción | El cliente no contiene necesariamente el servidor ni sus datos; requiere investigación y una implementación separada cuando corresponda |

**Diferencia decisiva:** no tener el editor de Unity no significa que el APK carezca de Unity. `libunity.so`, `libmono.so`, las DLL y los datos serializados contienen la parte distribuida del runtime, no el entorno de autoría.

## 8. Riesgos y trabajo de reimplementación

1. **Multijugador/backend.** Photon/PUN está presente, pero aún hay que reconstruir estados, eventos, RPC, autenticación, salas y persistencia. Cambiar un hostname no recrea un backend. La DLL `Photon3Unity3D` inspeccionada no tiene TypeRef hacia UnityEngine, lo que la hace candidata a estudio aislado; no prueba que pueda reutilizarse sin restricciones ni que sea compatible con un servidor moderno.
2. **Interfaz.** NGUI y Unity UI no se traducen directamente a otra tecnología. Hay que preservar navegación, estado y disposición visual, no solamente exportar sprites.
3. **Comportamiento del motor.** Física, animaciones, coroutines, ciclo de vida y orden de ejecución condicionan el gameplay. Los stubs no reproducen esas semánticas.
4. **SDK antiguos.** Compras, anuncios, login, notificaciones y analítica añaden dependencias de plataforma y servicios; su presencia no confirma disponibilidad actual.
5. **Serialización.** Las relaciones entre MonoBehaviour, ensamblados, tipos y referencias de objetos deben preservarse si se modifica el build original.
6. **Derechos y credenciales.** Trabajar sobre copias autorizadas; no publicar claves ni confundir acceso técnico a assets/código con derechos de redistribución.

## 9. Plan recomendado por fases

### Fase A — preservar e inventariar

- Calcular hashes de APK/OBB originales y registrar versiones de herramientas.
- Mantener `unpacked` como entrada; crear salidas separadas para staging, decompilación y exportaciones.
- Preparar Data combinado, reensamblando fragmentos por índice numérico y validando tamaños según el tipo de archivo.
- Conservar inventario de procedencia, nombres originales y errores de lectura.

### Fase B — decompilar antes de modificar

- Abrir las 27 DLL como conjunto de referencias.
- Exportar los cuatro ensamblados de scripts; analizar Photon y SDK de forma selectiva.
- Seguir arranque, carga del OBB, carga de escenas, menú, movimiento, armas, guardado y conexión.
- Separar lógica independiente, dependencia Unity y dependencia de servicios.
- Decodificar Android con JADX/Apktool para entender el bootstrap y puentes de plataforma.

### Fase C — probar una extracción pequeña

- Empezar por `globalgamemanagers`, `level0` y recursos compartidos necesarios, con referencias disponibles.
- Inventariar objetos y resolver MonoScripts/MonoBehaviours.
- Exportar una muestra de textura, audio y malla; validar resultados antes de procesar todo el OBB.
- Escalar por lotes y registrar recursos que no puedan exportarse.

### Fase D — comprobar comportamiento

- Instalar el original en Android de laboratorio compatible y ubicar el OBB donde corresponda.
- Capturar `logcat`: distinguir fallo de ABI, recurso ausente, error de SDK y dependencia de servidor.
- Instrumentar solo los puntos que el análisis previo no explique.

### Fase E — decidir la estrategia del proyecto

- **Preservación del APK:** conservar Unity embebido y realizar cambios acotados y verificables en copias.
- **Reimplementación sin Unity:** producir primero una especificación funcional y un prototipo mínimo: una escena, movimiento, cámara y un arma. No intentar portar de golpe las DLL.
- **Recuperación orientada al editor:** tratar el resultado de AssetRipper como punto de partida sujeto a reparación y compatibilidad, no como proyecto original recuperado.

## 10. Estado del entorno inspeccionado

El host es **Linux x86_64**. Se encontraron `python3`, `file`, `strings`, `readelf`, Node.js y npm.

No se localizaron en el PATH `dotnet`, Java, `jadx`, `apktool`, `adb`, `aapt`, `aapt2`, `monodis`, `ilspycmd` ni `ghidra`. `python3 -m pip` indicó que pip no está disponible para ese intérprete. Esto no descarta instalaciones fuera del PATH.

No se instaló el stack de ingeniería inversa durante este análisis. Se utilizó el CLI de Context7 vía `npx` únicamente para consulta documental.

## 11. Fuentes técnicas consultadas

- Unity 5.3, scripting backend IL2CPP/Mono: https://docs.unity3d.com/530/Documentation/Manual/IL2CPP.html
- ILSpy e ILSpyCmd: https://github.com/icsharpcode/ILSpy
- AssetRipper, soporte de versiones: https://github.com/AssetRipper/AssetRipper
- AssetRipper, scripts y problemas comunes: https://github.com/AssetRipper/AssetRipper/blob/master/docs/articles/CommonIssues.md
- UnityPy, instalación, extracción y type trees: https://github.com/K0lb3/UnityPy
- AssetStudio, formatos y exportaciones: https://github.com/Perfare/AssetStudio
- JADX: https://github.com/skylot/jadx
- Apktool: https://apktool.org/ y https://apktool.org/docs/cli-parameters/
- Android SDK CLI: https://developer.android.com/tools
- Firma APK: https://developer.android.com/tools/apksigner
- Frida para Android: https://frida.re/docs/android/
- Ghidra: https://github.com/NationalSecurityAgency/ghidra
- dnSpyEx: https://github.com/dnSpyEx/dnSpy

Las recomendaciones se apoyan en estas capacidades documentadas. La compatibilidad concreta de cada herramienta con este juego sigue requiriendo pruebas; no se presenta como ya validada.
