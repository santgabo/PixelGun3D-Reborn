# Compiled-logic first pass — original 11.3.1 menu/shop

## Identity and scope
Research only; no game execution, services contacted, downloads/installs, original-file modifications, or active-target lifecycle/analysis calls. Resource/scene investigation belongs to the other worker. No release year is established here.

Source: `/Users/santgabo/Projects/PixelGun3D/Pixel Gun 3D [11.3.1].apk`, supplied SHA256 `2e78ca8a1745f0d3052a8c327fd9bd5731de5499992bb9d8e928893b7ea52f25`, inventory `ev_d4eeffe18b167c43a6ab09048673d652b1ac1f7030a0a949627e13d55b4cbc69` (provided, not reproduced). Python zipfile extracted only four selected DLLs into `/var/folders/2c/pn00rp4d603djszy1j1njf5w0000gn/T/pg3d-logic-epbwll01/`; `identity.json` records archive/member/path/size/hash. All assembly member paths below are under `assets/bin/Data/Managed/`.

Principal DLL: `Assembly-CSharp.dll`, 5,514,240 bytes, SHA256 `57315485ae231478b42ae6b67203ba4e09bb52465d1b0cbdd1becfdc4c0bc93b`, MVID `e386a7f8-ee75-4760-8582-2de4c49e8b76`. Evidence A establishes assembly version **11.3.1.1191**, Unity Mono, IL-only/AnyCPU (the PE machine field alone says x86; it does not make the managed game x86-only), complete metadata: 3,396 type definitions and 25,597 method definitions.

## Evidence ledger
- **A** `ev_fbd8a64ab35c21f6b0b8745a657966a4827bab22504540abe0604e685fcbd49e`: managed artifact identity/classification.
- **B** `ev_d85e4d83eea79a05037dac012d3cb5e2c0dc6c1d28b302e7d965e65c01e72d2c`: MainMenuController selected members, bodies, call edges and strings. 149 methods; complete selected-member coverage.
- **C** `ev_668e72a35a126da0a1d9f9efb7e360f07f5c56bd28839e7057af9506869cdcac`: Initializer, MenuSceneLoader, Rilisoft.SceneLoader, ShopNGUIController, BankController, Storager and `<Start>c__IteratorBD`. Complete selected-member coverage; user-string coverage partial (15 terminal-flag inconsistencies; readable UTF-16 preserved; no runtime-acceptance conclusion).
- **D** `ev_e71c8104fec9e74613c22b2ec2cb06b27c72f9ec3df952b6822a9656fa25c0ea`: native boundaries.
- **E** `ev_8c17f53db58bf259337916459e61fcd32f88e2e95a40f7e4a26f1808d1827553`: MainMenu, UIRoot, UIPanel, UILabel. Complete selected-member coverage; three user-string terminal-flag issues.
All tokens below are build-local to the principal DLL/hash/MVID. REA decoded CIL without loading/resolving/executing the assembly. Call edges establish instructions, not actual invocation or branch outcomes.

## Observed menu/shop logic
**UI is NGUI-style Unity UI, not merely inferred from UnityEngine.UI.dll presence.** B/C contain calls to UILabel, UITexture, UIGrid, UIScrollView, UIPanel, UIButton, NGUITools and EventDelegate; E confirms UIRoot/UIPanel/UILabel definitions in this DLL. Shop also calls HOTween tween APIs and character/model-preview logic. Preserve these original controls and controllers rather than redraw a lookalike.

- `MainMenuController.Awake` (`0x06001aa1`, 140 CIL bytes) calls training state, PetsManager.LoadPetsToMemory, PrefabHandler.ResourcePath and LazyObject constructors.
- `MainMenuController.Start` (`0x06001ab3`) constructs `<Start>c__IteratorBD`; its `MoveNext` contains Resources.Load/Instantiate/DontDestroyOnLoad calls, button-handler subscriptions including HandleShopClicked and HandleBankClicked, synchronization/task-completion checks, platform checks, promotions and name/training-state logic. C contains this original coroutine body; it must not be mistaken for a 15-byte empty Start implementation.
- `MainMenu.Awake/Start` additionally call WeaponManager.Reset, FriendsController.InitOurInfo/WaitForReadyToOperateAndUpdatePlayer, StoreKitEventListener state and preferences (E). Scene attachment and relative ordering of MainMenu versus MainMenuController remain unknown.
- `MainMenuController.HandleShopClicked` (`0x06001ae5`, 178 bytes) contains calls to ShowBannerOrLevelup, training flags, Defs.ShouldEnableShopSN/PlayerPrefs.GetInt, UnequipSniperRifleAndArmryArmoIfNeeded, ShopNGUIController.SetInGame and set_GuiActive, plus a HandleResumeFromShop delegate. This supports an existing menu-to-armory activation route, not proof of a separate shop scene.
- `ShopNGUIController`: Awake `0x060046da` (1,280 bytes), Start `0x060046f3` (208), set_GuiActive `0x0600470f` (1,690), TryToBuy `0x06004625` (197), ActualBuy `0x060046e8` (1,359). Bodies are present. C edges include ItemDb/ShopItem, WeaponManager, Wear, gadgets, pets/eggs, price containers, equipment, UI carousel and grid, bank, analytics, and PurchasesSynchronizer. Original inventory/equip/purchase logic exists, not just artwork.
- Currency/IAP window is `BankController`; MainMenuController.ShowBankWindow (`0x06001acc`) calls BankController singleton/interface-lock checks, registers BackRequested and sets InterfaceEnabled. Armory and bank should be investigated separately.

## Initialization/navigation: partial, not a proven full boot chain
`Rilisoft.SceneLoader.LoadScene` (`0x060041bd`) and LoadSceneAsync (`0x060041be`) call GetSceneInfo, populate SceneLoadInfo and delegate to UnityEngine.SceneManagement.SceneManager.LoadScene/LoadSceneAsync; async also starts WaitSceneIsLoaded. `MenuSceneLoader.Awake` (`0x06002c51`) is only 35 bytes with field/null-test/component-resolution anchors; its name does **not** prove it boots the menu.

`Initializer` is substantially gameplay/network related: Awake loads scene/resources; Start has Network/Photon instantiate/connect calls. It must not be assumed to be the menu bootstrap just because of its name. Exact names `Starter` and `Rilisoft.Starter` did not match principal-assembly types; the raw identifier was only a search lead. Actual first-scene bootstrap and pre-menu coroutine remain unresolved pending scene bindings/other DLL inspection.

## Desktop blockers and recovery assessment
**Observed dependencies, not demonstrated blockers:**
- D records 507 P/Invoke declarations targeting module `gpg` (Google Play Games functions), no mixed-mode/native header. These Android native APIs need guarding/adaptation if reached on desktop; declarations alone do not prove menu initialization calls them.
- Main menu startup coroutine includes Editor/Google/Amazon synchronization dispatch, GameCenterSingleton, authentication/achievement work, trophy/skin/pet synchronization, and Task completion predicates. Static edges identify potential offline/platform waits; whether any prevents rendering requires branch/coroutine reconstruction.
- Storager.hasKey/getInt/getString/setInt/setString call CryptoPlayerPrefsFacade, PlayerPrefs, SaltedInt and DigestStorager. PurchasesSynchronizer.AllItemIds appears in static initialization. A faithful local state must respect key/default/digest/migration behavior rather than invent balances. Crypto facade internals and existing save requirements were not traced.
- Shop calls promo/temp-item/premium/account and purchase synchronization systems. Missing network data could affect catalog/promotions/prices, but no mandatory live-server gate is proven.
- Initializer.InitializeSeparator uses AndroidSystem.CurrentActivity and AndroidJavaObject.Call/Get, but belongs to the examined gameplay/network subsystem; menu reachability is unproven.

**Inference:** substantial original logic is recoverable as named managed CIL, including actual menu/armory methods and coroutines. This is materially better than recreating UI from screenshots. AnyCPU CIL is not itself the Android-portability blocker. Matching Unity runtime, serialized scene/prefab/component bindings, original NGUI, resource loading and platform wrappers are the larger integration concerns. No percentage or turnkey desktop feasibility can be justified yet. APK Android libunity/libmono are not desktop engines.

## Coverage limits and next minimal probe
No C# decompiler executable was available on PATH (`ilspycmd`, `monodis`, `dotnet`, `ildasm` absent); none installed. REA yielded CIL anchors/hashes/call edges, not reconstructed C# or verified control flow. Only principal-assembly selected types were decoded; three other extracted DLLs remain uninspected. No native exports, DEX/plugin implementation, runtime behavior, resource completeness or visual fidelity was tested.

**Next minimal probe:** take the resource worker's first-scene MonoBehaviour bindings, then inspect only their exact declaring types (including other managed DLLs if necessary). Reconstruct the first-scene coroutine and `<Start>c__IteratorBD.MoveNext` branch/yield path up to original menu activation, with particular attention to platform/synchronization completion predicates. This resolves the highest-risk unknown—whether the original menu can initialize offline—without implementing replacement UI or investigating maps/gameplay.
