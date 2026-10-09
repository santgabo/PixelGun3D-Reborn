# Mapa de dependencias Mono — PASS acotado

Corrida **20261009T191951Z**, ILSpyCmd **11.1.0.9782**. Origen: las 27 DLL originales de `unpacked/apk/assets/bin/Data/Managed`; hashes en `RUN/managed/inputs.json`. `RUN` = `.lab/runs/20261009T191951Z/` (privado, no versionado).

## Decompilación

Listados de clases/interfaces/estructuras/delegados/enums y proyectos separados, secuenciales, usando `-p -r MANAGED -o ...`; no se compiló ni ejecutó el C#.

| Ensamblado | Archivos C# | Listado / proyecto | Diagnósticos detectados |
|---|---:|---|---:|
| Assembly-CSharp | 1.778 | rc0 / rc0 | 0 |
| Assembly-CSharp-firstpass | 182 | rc0 / rc0 | 0 |
| Assembly-UnityScript | 11 | rc0 / rc0 | 0 |
| Assembly-UnityScript-firstpass | 11 | rc0 / rc0 | 0 |

Los ocho stderr están vacíos. Registro por ensamblado, cobertura y patrones de búsqueda: `managed/inspection.json`; comandos/salidas/rc: `logs/mono-*.{json,stdout,stderr}`. **Cero diagnósticos detectados no demuestra exactitud de todos los métodos**; archivos C# no equivalen a entradas TypeDef y UnityScript representado como C# no recupera su fuente original.

## Dependencias directas recuperadas

Origen: `managed/<ensamblado>/<ensamblado>.csproj` y referencias explícitas de tipos/métodos.

- `Assembly-CSharp`: UnityEngine, Assembly-CSharp-firstpass, System.Core, Unity.Tasks, Photon3Unity3D, FyberPlugin, HOTweenMicro, FyberLitJson, ArabicSupport, UnityEngine.UI, P31RestKit, System.Xml.Linq y Assembly-UnityScript-firstpass. La lista exacta, con grafía del exportador, está en `inspection.json`; no se sustituyeron referencias por DLL modernas.
- `Assembly-CSharp-firstpass`: UnityEngine, System.Core, DecalSystem.Runtime y P31RestKit.
- `Assembly-UnityScript`: UnityEngine, Boo.Lang y UnityScript.Lang.
- `Assembly-UnityScript-firstpass`: UnityEngine y Boo.Lang.

## Clasificación con evidencia

| Subsistema | Clasificación | Evidencia concreta en Assembly-CSharp, salvo indicación |
|---|---|---|
| Igualdad de categorías | Lógica aislable candidata | `WeaponManager.WeaponTypeForLowComparer.Equals/GetHashCode`: comparación/cast de enum. No se ha probado su reutilización fuera del juego. |
| Movimiento | Dependiente de Unity | `FirstPersonControlSharp.Update/Update2`: joystick, Time.deltaTime, gravedad y CharacterController.Move; `Player_move_c.Awake/Start/FixedUpdate/Update`: estado local/remoto, objetos, coroutines y Rigidbody. |
| Armas | Dependiente de Unity | `WeaponManager.Awake/Start/AddAmmo`, `WeaponSounds.Initialize/Start/fire`: prefabs, GetComponent, recursos, animación y munición. |
| Android/expansión | Puente Android | `Assembly-CSharp-firstpass::GooglePlayDownloader.GetExpansionFilePath/GetMainOBBPath/FetchOBB`: AndroidJavaClass/AndroidJavaObject hacia Environment y UnityDownloaderActivity. |
| Photon/PUN | Dependiente de backend y Unity | `PhotonNetwork.ConnectUsingSettings`, `PhotonView.Awake/RPC`: registro en NetworkingPeer, configuración ServerSettings, conexión y RPC. La rama OfflineMode existe, pero no se ha probado que sea la configuración activa ni que permita gameplay offline. |
| Arranque | Dependiente de Unity/plataforma | `AppsMenu.Awake/Start/AppsMenuAwakeCoroutine`, `Launcher.Awake/Start/InitRootCoroutine`, `MenuSceneLoader.Awake`, `ConnectSceneNGUIController.Awake/Start`. La presencia de Launcher no demuestra que esta copia lo use al iniciar; ver [flujo real](flujo-arranque.md). |

## Contraste C# / IL

Tres contrastes selectivos, sin discrepancia en los comportamientos siguientes:

- `FirstPersonControlSharp.Update2`, RVA **0x1b37e8**: salida si collider deshabilitado; Move en IL_0063/IL_00e2; rama de hielo y reinicio de velocity al estar en suelo.
- `WeaponManager.AddAmmo(Int32)`, RVA **0x17170c**: índice -1, excepción de melee, incremento por tipo y límite MaxAmmoWithEffectApplied.
- `PhotonNetwork.ConnectUsingSettings(String)`, RVA **0xbba24**: exige Disconnected/configuración, rama OfflineMode, SelfHosted/BestRegion/conexión regional.

Evidencia: `managed/il/{movement,weapons,network}.il` y `origins.json`, con rangos de líneas en la salida IL original. **Limitación de la CLI instalada:** `-il` produjo IL del ensamblado completo aun con `-m` o `-t`; no se confundió rc0 con selección correcta. Se conservaron esos logs y se extrajeron los métodos por su identificador `tipo::método`. No se decompiló el motor completo ni otros SDK por rutina.

## Límites

No se verificó cada método contra IL, no se reprodujeron semánticas del motor ni se contactó un backend. Una clasificación es una interpretación de dependencias observadas, no una garantía de portabilidad. SDK encontrados sin una llamada relevante siguen sin análisis exhaustivo.
