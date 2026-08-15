# Third-party Unity assets (local only)

Place downloaded free packs under this folder. Do **not** commit large binary packages to GitHub unless explicitly approved.

## Imported packs (current)

| Folder | Role | Source |
|------|------|--------|
| `SapphiArt/` | Sakura visual (`SapphiArtchan` / Amane Kisora) | Unity Asset Store #70581 |
| `Asuna/` | Previous Sakura candidate (unused) | Unity Asset Store #205897 |
| `CosmicRetroStation/` | Station props (consoles, monitors, crates…) | Unity Asset Store #323347 |
| `CobbleGames/` | Background Space Station modules | Unity Asset Store #188734 |
| `UnityChan_SSU/UnityChanSSU/` | Player scientist visual | unity-chan.com Sunny Side Up URP |

## Scene wiring

- Sakura: `NPC_Star/Visual/Sakura_Sapphi` + `Resonance_Aura`
- Player: `Player/Visual` (Unity-Chan prefab)
- Station props: `Environment_NebulaStation/Imported_Props`
- Sakura animator: `Assets/_Project/Art/Characters/Sakura/Sakura_SapphiArt.controller` (Wave / Angry / Think)

## Notes

- SapphiArt materials were converted to `Toon/Toon` (outline off) to match Unity-Chan.
- Built-in `Standard` materials under station packs were converted to `Universal Render Pipeline/Lit` on import.
- Prop colliders on the approach path were removed so Player movement stays clear.
- Nested leftover folders from Unity-Chan zip extraction may still exist under `UnityChan_SSU/`; safe to ignore or delete manually in Unity.
