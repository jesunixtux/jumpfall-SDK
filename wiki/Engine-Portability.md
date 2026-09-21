# Engine portability and console preparation

JumpFall currently ships from one Unity 6.3 implementation. This page describes
the boundaries added to prepare a possible console implementation without
replacing the PC build or promising a port.

## Portable data versus Unity implementation

Portable contracts:

- JMAP/JFUE `LevelData` version 29;
- stable `objectId` references for pieces, triggers, backgrounds, bosses and
  ghosts;
- boss pattern graph and boss animation data;
- SaveData versions 1, 2 and 3;
- `assetlocal` and legacy `assetslocal` folder conventions;
- capability and storage interfaces.

Unity-specific implementation:

- `RuntimeLevelBuilder` and prefab/component instantiation;
- Unity scene names and Build Settings;
- `PlayerMovement`, Rigidbody2D, Animator and Input System behavior;
- Steamworks.NET, overlays and Workshop callbacks;
- Unity UI used by both Level Editors.

The JSON schemas are available at:

```text
Tools/jumpfall-sdk/schema/jumpfall.map.schema.json
Tools/jumpfall-sdk/schema/jumpfall.save.schema.json
Tools/jumpfall-sdk/schema/jumpfall.runtime-build-report.schema.json
```

## Platform capabilities

Code should query `IPlatformCapabilities` through
`JumpfallPlatformRuntime.Capabilities` instead of assuming all standalone builds
are Steam builds.

Available flags:

- `SupportsLevelEditor`
- `SupportsUserGeneratedContent`
- `SupportsWorkshop`
- `SupportsLocalSkins`
- `SupportsMods`
- `SupportsAchievements`
- `SupportsCloudSave`
- `SupportsMultiplayer`
- `SupportsDeveloperConsole`
- `SupportsQuitButton`

`PcCurrent` is the default and preserves current PC behavior.
`ConsoleRestricted` hides the editor, UGC, Workshop, local skins, mods, the
developer console and the quit button. Achievements and cloud save remain off in
that profile until real platform providers exist. Multiplayer remains a
capability but is still gated by the existing `JUMPFALL_MULTIPLAYER` build flag.

The restricted profile can be smoke-tested on PC:

```text
-jumpfall_platform_profile=ConsoleRestricted
-jumpfall_storefront=ConsoleGeneric
```

This is only a capability simulation. It is not a console SDK implementation.

Profile and storefront are validated as one configuration. The supported matrix
is deliberately small:

| Profile | Supported storefronts | Default |
| --- | --- | --- |
| `PcCurrent` | `Steam` | `Steam` |
| `ConsoleRestricted` | `ConsoleGeneric`, `None` | `ConsoleGeneric` |

An incompatible combination is rejected by the validator and normalized to the
profile default before capabilities or platform services are resolved.
`PcCurrent/None` is intentionally invalid because the current PC capability set
exposes Steam Workshop, achievements and cloud save. `ConsoleRestricted/None`
remains available for storefront-free tests and already hides those features.

## Forward-version protection

This build supports maps through v29 and saves through v3. A higher version
returns `UnsupportedFutureVersion` before full deserialization or migration.
The original file is not normalized, relabeled, saved or deleted.

Saving also checks the existing destination header. A current build refuses to
overwrite a map or save created by a future build.

## PlayerMovement boundary

`PlayerMovement` remains the gameplay authority and was intentionally not
refactored. A future implementation must first reproduce its serialized tuning,
including:

- `moveSpeed`, `sprintMultiplier`, `jumpForce`, `maxJumps`, `gravityScale`;
- acceleration, deadzones, jump cut and ramp rules;
- climbing-wall slide and wall-jump values;
- dash speed, duration, cooldown, grace and post-dash jump lock;
- jetpack duration and force;
- damage, invulnerability, knockback, life and respawn values;
- external launch blending and gamepad feedback.

The values are a compatibility surface, not permission to change game feel in a
portability refactor.

## Injectable platform services

`ISaveStorageProvider` creates `ISaveStorage` from a context containing the
active profile, storefront and current paths. The default PC provider keeps the
existing paths and migration behavior:

```text
Documents/jumpfall/save/savegame.json
Application.persistentDataPath/savegame.json  (legacy migration source)
```

Future console storage can inject a provider for the session and ignore the
filesystem path hints. `PickupCounterManager` PlayerPrefs data is intentionally
unchanged; it must not be destructively migrated as part of this work.

`IAchievementServiceProvider` resolves the achievement service from the active
profile and storefront. The default provider still composes the existing Steam
and JevzGames adapters. Injecting a provider does not modify either integration.

## Logical scene catalog

`JumpfallSceneId` identifies runtime destinations such as the desktop menu,
mobile menu, campaign start, both editors and the compiled-map template.
`IJumpfallSceneCatalog` maps those IDs to Unity scene names and can be replaced
for a test or future platform.

Serialized scene fields remain explicit overrides. JMAP/JFUE v29 and SaveData v3
still store their existing values, including `SaveData.sceneName`; the catalog
does not migrate or rewrite persisted data.

## RuntimeLevelBuilder behavior fixture

`RuntimeLevelBuilder.BuildWithReport` invokes the same construction path as
`Build` and records a neutral ordered result. It reports built, missing, rejected
and editor-suppressed entries without serializing Unity components.

Cross-engine fixtures are stored at:

```text
Tools/jumpfall-sdk/fixtures/runtime-builder/runtime-builder-v29.jmap
Tools/jumpfall-sdk/fixtures/runtime-builder/runtime-builder-v1.catalog.json
Tools/jumpfall-sdk/fixtures/runtime-builder/runtime-builder-v1.expected.json
```

A future Godot implementation should consume the map and neutral catalog, emit
the report schema above, and compare every ordered record against the expected
JSON. This fixture is a compatibility check, not a second map format.

## Future format candidates, not implemented

- SaveData v4 with a logical `levelId` or `mapId`;
- a ghost-frame `animationId` independent from Unity Animator hashes.

Any of these requires a new version, fixtures, migrations and an explicit stop
before changing production files.
