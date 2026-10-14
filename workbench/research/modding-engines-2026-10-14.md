# Repositories that handle game modding across engines (Lua and others)

Date: 2026-10-14. Every row below was checked against the GitHub API on that
day (`gh api repos/<owner>/<name>`): stars, licence, last push and description
are observed values, not recollection. Two 404s are listed as such. Nothing in
this page was installed into the game or into any owner repository.

Question it answers: *which repositories already handle "engines like Lua and
many other engines", and what applies to a SUGAR/Lua game such as Shotgun
King?* The companion experiment is
`workbench/projects/shotgun-king-anew/REA_MOD_SAFETY_EXPERIMENT_2026-10-14.md`.

## 1. Agent-facing, multi-engine toolkits (the direct answer)

| Repository | Stars | Licence | Last push | What it is | Lua coverage |
|---|---|---|---|---|---|
| `rehan-remade/universal-modder` (the owner has a fork) | 7,437 | MIT | 2026-10-13 | 12 Agent-Skills (`mod-any-game`, `game-recon`, `reverse-engineering`, `game-automation`, `port-a-mod`, …), a `um` CLI, and a knowledge base of **82 game field notes**. `mod-any-game` carries **14 engine playbooks**: Unity, Unreal, .NET/XNA, Godot, Source, Bethesda, Minecraft, native, retro decomp, Bannerlord, Genie (AoE2), ZenGin, "big frameworks" (RE Engine, MT Framework, FromSoftware, RAGE, Hedgehog, REDengine, Frostbite, Larian, Paradox/Total War), and `misc-engines.md`. Installs into Claude Code, Codex, Gemini CLI, Copilot, Cursor, OpenCode. | `misc-engines.md` §"LÖVE (Lua)" (unzip the `.love`/appended zip, read the Lua; **lovely** runtime patching + Steamodded for Balatro), Defold (`game.arcd`, Lua), Cocos2d-x (Lua/JS, XXTEA), Project Zomboid (Lua + Java), DFHack (Lua scripts). No SUGAR/PICO-8-style engine section. |
| `morluto/rea` (the owner has a fork, `rea-fork`) | 214,211 | MIT | 2026-10-14 | "Reverse engineer anything with agents": MCP server + CLI (`rea`, 6.4.0 on npm) over Hopper/Ghidra/IDA, JS/Electron, .NET, APK, web, **process capture**, Evidence records, reconstruction obligation ledgers. Not a modding tool; the evidence discipline that modding verification needs. | No Lua analyzer. Process capture and the ledger are language-agnostic (used in the experiment). |
| `Freakmenn/ai-game-modding-guides` (owner fork) | 1 | MIT | 2026-10-09 | Prose guides for two project kinds built with an agent harness: passthrough mods (two games linked, e.g. Minecraft inside Skyrim) and Rust rewrites/ports. Starter `AGENTS.md`, legal/takedown notes. | None specific. |

`universal-modder` also states the verification doctrine this workbench already
uses: *"The running game is the oracle; your reading of the code is not"*
(`skills/mod-any-game/SKILL.md` §7), with a circuit breaker after three
identical failures, and a knowledge-base rule of *no game files, no decompiled
dumps, an honest status and verification*.

## 2. Per-engine mod loaders that expose a Lua scripting surface

| Repository | Stars | Licence | Last push | Engine / games | Lua role |
|---|---|---|---|---|---|
| `UE4SS-RE/RE-UE4SS` | 3,004 | MIT | 2026-10-13 | Unreal Engine 4/5 | "Injectable LUA scripting system, SDK generator, live property editor" |
| `praydog/REFramework` | 5,632 | MIT | 2026-10-11 | Capcom RE Engine | Mod loader + Lua scripting platform + VR |
| `ethangreen-dev/lovely-injector` | 610 | MIT | 2026-09-23 | LÖVE | Runtime Lua patch injection (no repacking) |
| `Steamodded/smods` | 989 | GPL-3.0 | 2026-10-13 | Balatro (LÖVE) | Lua mod loader on top of lovely |
| `DFHack/dfhack` | 2,051 | NOASSERTION (zlib-style, check file) | 2026-10-13 | Dwarf Fortress | Lua scripts + C++ plugins over a memory-hacking library |
| `cheat-engine/cheat-engine` | 19,315 | none declared | 2025-04-19 | any native Windows process | Lua-scriptable memory tooling |
| `thegrb93/StarfallEx` | 212 | NOASSERTION | 2026-10-09 | Garry's Mod (Source) | Sandboxed Lua chips |

## 3. Generic loaders and patchers (not Lua, but the "many other engines")

| Repository | Stars | Licence | Last push | Scope |
|---|---|---|---|---|
| `BepInEx/BepInEx` | 8,835 | LGPL-2.1 | 2026-09-20 | Unity / XNA patcher + plugin framework |
| `LavaGang/MelonLoader` | 4,255 | Apache-2.0 | 2026-10-06 | Unity (Il2Cpp and Mono) |
| `pardeike/Harmony` | 6,685 | MIT | 2026-10-11 | Runtime patching of .NET/Mono methods |
| `Reloaded-Project/Reloaded-II` | 1,045 | GPL-3.0 | 2026-09-23 | .NET-powered framework for any native x86/x64 game |
| `Pathoschild/SMAPI` | 2,757 | LGPL-3.0 | 2026-09-28 | Stardew Valley |
| `tModLoader/tModLoader` | 5,724 | MIT | 2026-10-14 | Terraria |
| `FabricMC/fabric-api` | 3,196 | Apache-2.0 | 2026-10-13 | Minecraft (Fabric) |
| `neoforged/NeoForge` | 2,092 | LGPL-2.1 | 2026-10-12 | Minecraft (Forge lineage) |

## 4. Analysis and instrumentation (engine-agnostic)

| Repository | Stars | Licence | Last push | Use |
|---|---|---|---|---|
| `frida/frida` | 22,267 | NOASSERTION (wxWindows) | 2026-10-13 | Dynamic instrumentation of any process |
| `NationalSecurityAgency/ghidra` | 86,484 | Apache-2.0 | 2026-10-13 | Static RE (REA has a Ghidra provider) |
| `radareorg/radare2` | 25,030 | NOASSERTION (LGPL-3.0) | 2026-10-13 | CLI RE framework |
| `x64dbg/x64dbg` | 49,854 | NOASSERTION (GPL-3.0) | 2026-10-09 | Windows user-mode debugger |

## 5. Lua bytecode and source tooling (for games that ship compiled Lua)

| Repository | Stars | Licence | Last push | Note |
|---|---|---|---|---|
| `viruscamp/luadec` | 1,334 | none declared | 2024-02-25 | Lua 5.1/5.2/5.3 decompiler |
| `HansWessels/unluac` | 254 | NOASSERTION | 2015-07-11 | Mirror of the SourceForge unluac (Java); stale |
| `marsinator358/luajit-decompiler-v2` | 487 | NOASSERTION | 2026-05-14 | LuaJIT bytecode decompiler |
| `Aussiemon/ljd` | 81 | GPL-3.0 | 2023-06-12 | LuaJIT raw-bytecode decompiler (the `NightNord/ljd` origin returns 404) |
| `mpeterv/luacheck` | 2,051 | MIT | 2022-12-18 | Lua linter / static analysis (useful for a mod CI lane) |

Lua game engines themselves, for completeness: `love2d/love` (8,826, zlib,
2026-09-20), `defold/defold` (6,372, NOASSERTION, 2026-10-13), `nesbox/TIC-80`
(6,162, MIT, 2026-10-13). Not found: `rehan-remade/ai-game-modding-guides`
(the owner's fork descends from `Freakmenn`), `NightNord/ljd`,
`bobsayshilol/luajit-decompiler`, `lua-rocks/luacheck`.

## 6. What this means for Shotgun King (SUGAR engine, Lua 5.1/LuaJIT)

Observations from the owner's `shotgun-king-anew` repository (`4c4bf1b`):
the game is a custom engine (SUGAR) that loads mods as plain `script.lua` +
`info.lua` with an additive hook API; no loader injection is needed; the
mod's danger zone is the engine's own globals (`remove_buts()`, the board click
path, `all()` iterator semantics).

- Nothing in §1–§5 has a SUGAR playbook. The nearest neighbours are
  universal-modder's LÖVE section (plain Lua you can read; the engine is the
  oracle) and its `game-automation` skill (launch, screenshot, click, read the
  log) — that is the shape of the live-game test the owner's run 5/6 already
  did by hand.
- `lovely-injector`'s model (patch Lua at load time, never repack) is not
  needed: SUGAR already loads mod Lua directly.
- `luacheck` is the one tool that would add a cheap, honest gate today: a
  static pass over `script.lua` for undefined globals, which is exactly the
  class of mistake (`remove_buts`, `mcl`) that bit builds 6–7. Not installed
  here; recommendation only.
- REA contributes the evidence discipline, not a Lua analyzer. The experiment
  page shows what that buys and where it stops.

Candidate lane for this workbench, still **not** built (no second Lua project
to calibrate on): `lua-game-modding` = universal layer + a UI↔engine
behaviour-contract table per panel + the repo's lupa harness as the
integration verifier + a luacheck gate.

## Not verifiable here

- Star counts and licences are a snapshot; licence `NOASSERTION` means GitHub
  could not classify the file, not that the project is unlicensed — read the
  file before reusing code.
- None of the loaders in §2–§3 were run; the rows describe what each
  repository says it does. Only `universal-modder`, `ai-game-modding-guides`
  and `rea` were cloned and read.
- Whether SUGAR's `all()` yields values or (index, value) pairs is still an
  open question in the owner's notes; see the ledger's residual unknown.
