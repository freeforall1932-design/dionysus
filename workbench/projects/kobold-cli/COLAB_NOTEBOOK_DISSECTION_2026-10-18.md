# KoboldCpp Colab notebook — dissection & verdicts (2026-10-18)

> **Purpose:** check, against primary source, another AI model's claim that
> the official KoboldCpp Colab notebook is missing advanced form fields a
> coding user would need, and define what a fine-tuned notebook for this
> project should keep, drop, and add.
>
> **Sources read (2026-10-18):** `LostRuins/koboldcpp`, branch `concedo`,
> commit `f41f621e09822cc6ba48f3d791c41c239ebb6335` (dated 2026-10-17):
> the notebook file `colab.ipynb` (all 4 cells) and the argument/logic
> sections of `koboldcpp.py`. Notebook opened the linked way at
> <https://colab.research.google.com/github/LostRuins/koboldcpp/blob/concedo/colab.ipynb>.
> Nothing was run on Colab. Colab terms/limits are **not** answered here —
> that stays open as W-021 / Q14 in
> [the AI Team Kit worklist](../ai-team-kit/WORKLIST.md).

## 1. What the official notebook actually is

Four cells:

1. An "Open in Colab" badge (empty after it).
2. Welcome/setup instructions (pick GPU runtime, set options, press play,
   wait for the tunnel link; keep the tab open and watch for captchas).
3. A **silent-audio keep-alive cell** whose stated purpose is preventing
   Colab from disconnecting the runtime. (Flagged: this "stay alive"
   design is exactly the kind of thing W-021/Q14 must check against
   current Colab terms before any real use.)
4. One big form + launch cell (291 lines). It installs `aria2`, optionally
   wipes old model files, downloads the **latest unpinned** Linux binary
   from GitHub releases (fallback: a mirror), builds one fixed launch
   command, and runs it with a Cloudflare remote tunnel.

The form is roleplay-oriented. Its 39-model dropdown is mostly RP and
uncensored finetunes (plus a few general models); its 15 one-click
"templates" bundle model + vision + image + speech + TTS combinations.
Beyond the text model, the form covers: GPU layers (Auto or 999), context
size (dropdown 4,096–40,960, custom values allowed; templates go to
49,152), vision projector, image generation (several), speech-to-text,
text-to-speech, embeddings, music generation, delete-old-models
(**default ON** — every run re-downloads the model), multiplayer, Google
Drive save-folder, and a localtunnel fallback.

The final command is **fixed**: `--usecuda 0 --gpulayers <n> --contextsize
<n> --websearch --quiet --remotetunnel` plus per-feature fragments. There
is **no free-form arguments field**, and the finished command is not shown
to the user before it runs.

## 2. Verdicts on the four claimed gaps

### Claim 1 — "No `--flashattention`; crucial, must be added" → ❌ REJECT (outdated)

- In current KoboldCpp there is **no enable-flag to add**: flash attention
  is **ON by default**. The only flag is the off-switch
  `--noflashattention` ("Disables flash attention"), and the loader sets
  `flash_attention = True` unless that flag is present.
- The notebook never passes the off-switch, so notebook users already get
  flash attention. Nobody needs to edit the cell to "turn it on".
- The underlying benefit is real (lower attention memory at long context,
  and full KV-cache quantization requires it — see claim 2), and a
  fine-tuned form should still expose an **on/off toggle** because the
  off-switch exists for models/backends that misbehave with it. But as
  stated — absent and crucial to add — the claim is wrong.
- Not verified here: flash-attention behaviour on the specific free-tier
  GPU (commonly a 16 GB T4, not guaranteed). First real run must confirm
  from the startup log that it activates cleanly.

### Claim 2 — "No `--quantkv`; required (e.g. `--quantkv 1`) for 16k+ context on 16 GB" → ✅ APPROVE the gap; correct the details

- The flag exists and the form genuinely lacks it. Valid values are
  `f16` (default), `bf16`, `q8_0`, `q5_1`, `q4_0`; the numeric form also
  works as a legacy alias (`1` = `q8_0`, `2` = `q4_0`, `3` = `bf16`), so
  the other model's example is valid but dated style.
- Why it matters (worked examples — formula: KV bytes/token ≈ layers ×
  KV-heads × head-dim × 2 (K+V) × bytes-per-value):
  - A Llama-3.1-8B-class model (32×8×128): ≈128 KB/token at `f16` →
    16k context ≈ 2 GB; `q8_0` ≈ 1 GB. With ~6–7 GB of Q6 weights this
    fits a 16 GB card **even without** KV quantization.
  - A Mistral-Small-24B-class model (40×8×128) at Q4_K_S (~14 GB
    weights): `f16` KV ≈ 2.6 GB at 16k (over budget), `q8_0` ≈ 1.3 GB
    (fits, tight), and long contexts like 40k need `q8_0`/`q4_0` or a
    smaller model. (Illustrative arithmetic; confirm against the KV
    buffer size KoboldCpp prints at load.)
- So "required for 16k+ on 16 GB" is **model-dependent**: overstated for
  7B–14B coding models, accurate for 24B+. The gap itself is real and
  cheap to expose; `q8_0` is the sane default (roughly half the KV
  memory, small quality risk; `q4_0` is the aggressive option).
- KoboldCpp requires flash attention for the full effect — without it
  only the K cache quantizes and it warns this is "NOT RECOMMENDED". Fine
  per claim 1: flash attention is already on.

### Claim 3 — "No advanced RoPE scaling / YaRN; only a basic context box" → ⚠️ PARTIAL (gap real, need oversold)

- True about the form: only `ContextSize` is exposed.
- But the engine's **default is NTK-aware RoPE scaling, set automatically
  from context size** (per `--ropeconfig` help), and the CLI also has
  `--ropeconfig <freq-scale> [freq-base]` and `--overridenativecontext`
  for manual control. There is no separate "YaRN" switch in the Python
  layer; YaRN in this stack is a model-file (GGUF metadata) property, not
  a notebook feature to bolt on.
- For coding, stretching a model past its trained context degrades
  quality under every scaling method. The right default is: pick a
  natively long-context coding model, run it at/below its trained
  context, leave scaling automatic. Manual RoPE fields are advanced
  escape hatches, not a requirement. Claim's framing ("required to
  maintain logic beyond native context") is rejected; the form gap is
  noted as low priority.

### Claim 4 — "No generic arguments field (e.g. `--mmq`)" → ✅ APPROVE the gap, ❌ REJECT the example

- Confirmed: no extra-args field; the launch line is hardcoded, so any
  unlisted flag means editing cell code. For a coding-focused notebook
  this is the single most useful addition (it future-proofs every other
  flag).
- But `--mmq` does not exist. MMQ (batched quantized matmul) is **on by
  default** for CUDA; `--nommq` disables it, and `mmq` can appear as a
  `--usecuda` mode token. The example flag needs no passing.

**Score: the other model was right that the form is missing controls, but
two of its four specifics are wrong for current KoboldCpp (flash
attention and MMQ are defaults, not missing enables), one is right with
dated syntax (quantkv), and one is real but low-value (RoPE). Always
check `--help`/source over second-hand flag lists.**

## 3. Other findings that matter for this project

- **No password by default.** The notebook publishes a public Cloudflare
  URL (`--remotetunnel`) without `--password` or `--adminpassword`.
  Anyone who gets the link can use (and administer) the endpoint.
  KoboldCpp supports both passwords (also via `KCPP_PASSWORD` /
  `KCPP_ADMINPASSWORD` env vars). A fine-tuned form must set them.
- **DeleteExistingModels defaults ON** → full model re-download each
  session. For a 10–20 GB coding model that is the slowest possible
  start; default it OFF.
- **Unpinned binary**: downloads `releases/latest` with no version pin or
  checksum. Our copy should pin a version and verify a hash (same rule
  as kit work item W-011).
- `--websearch` and `--quiet` are always on; web search proxy is
  unnecessary for an API endpoint. Make it opt-in.
- **Tool calling exists** in KoboldCpp's chat API (it parses model
  tool-calls), which is what a coding agent needs — but whether a given
  local model does it reliably is a runtime probe, not a docs answer.
- Useful engine options the form hides that suit this project:
  `--blasbatchsize` (prompt-processing speed vs VRAM for big file
  ingestion), `--genlimit` (hard cap on generated tokens — matches our
  quota-guard philosophy in W-015/W-050), `--parallelrequests` (default
  1 = queued; >1 allows concurrent council calls at VRAM cost and
  disables context shifting), `--draftmodel` (speculative decoding
  speed-up), `--benchmark` (speed checks without serving).

## 4. Fine-tuned form spec (only what this project needs)

Keep the one-cell shape, but rebuild the form for **"one private coding
endpoint while Colab is online"**:

| Field | Behaviour |
|---|---|
| Coding preset | Small dropdown of coding models that fit the VRAM math (e.g. 7B/14B/24B tiers), each preset = model URL + context + quantkv bundle |
| Model URL | Allow-input, prefilled by preset; any GGUF URL works |
| Context size | 8192 / 16384 / 32768 / 65536 (allow-input), default from preset |
| KV cache (`--quantkv`) | `f16` / `q8_0` (default) / `q5_1` / `q4_0` |
| Flash attention | Checkbox default ON; unchecked adds `--noflashattention` |
| GPU layers | Auto (-1 autofit) default; numeric override allowed |
| Batch size (`--blasbatchsize`) | 512 default / 1024 / 2048 |
| Password | Auto-generated per run and printed once (or owner-typed); sets `--password` + `--adminpassword` |
| Gen limit (`--genlimit`) | 0 = off (default); optional hard cap |
| Extra args | Free-text, appended last; **the full final command is printed before launch** |
| Delete old models | Default **OFF** |

Drop from the official form: image generation, TTS, speech-to-text,
music, multiplayer, vision projector, Drive story-saves, roleplay model
list/templates, always-on web search. Pin the KoboldCpp release version
+ verify its SHA-256. Keep the localtunnel fallback. Keep the keep-alive
cell **only if** W-021 clears it against current terms.

## 5. Tested / not tested

- **Read (not run):** every notebook cell; the argument definitions and
  loader logic for `--noflashattention`, `--quantkv`, `--ropeconfig`,
  `--overridenativecontext`, `--nommq`, `--usecuda`, `--password`,
  `--adminpassword`, `--blasbatchsize`, `--genlimit`,
  `--parallelrequests`, `--draftmodel`, `--benchmark` at commit
  `f41f621…`.
- **Not tested:** running the notebook or KoboldCpp anywhere; actual
  free-tier GPU model/VRAM; flash-attention activation on that GPU; real
  KV memory vs the §2 arithmetic; any model's tool-calling; tunnel
  reachability from Odysseus/OAT; Colab terms, session limits, and
  keep-alive acceptability (W-021/Q14 — still the gate before real use).

## 6. Implementation note (later on 2026-10-18; superseded by §7)

At the owner's explicit request, the fine-tuned form was implemented as
[`kobold-cli.ipynb`](kobold-cli.ipynb), with
[`COLAB_LINK.txt`](COLAB_LINK.txt) holding only the direct Colab URL. It
defaults to preflight-only (no download/tunnel), includes no keep-alive
cell, pins KoboldCpp `v1.123.1` with SHA-256 verification, pins the model
presets to Hugging Face revisions, binds the server to loopback inside
the runtime, and generates a fresh password in launch mode. Admin mode
remains off; the same generated secret is supplied through both password
environment variables so a later admin enable cannot silently start
unprotected. The notebook's default cells and download helper were
tested locally, but it still had **not run on Colab** when added, and
W-021/Q14 remains open before it is relied on.

## 7. Owner runtime correction and upstream-based rebuild (later on 2026-10-18)

The owner then ran the §6 custom notebook in real Colab and it failed
immediately:

```text
FileNotFoundError: [Errno 2] No such file or directory: '/content/kobold-cli'
```

Root cause: the custom preflight chose `/content/kobold-cli` for
`shutil.disk_usage()` merely because `/content` existed, before creating
the child directory. The earlier local test had not reproduced the exact
fresh-Colab state (`/content` exists, `/content/kobold-cli` does not).
That failure invalidates using the §6 design as the owner's test
notebook.

At the owner's correction, [`kobold-cli.ipynb`](kobold-cli.ipynb) was
rebuilt from the actual upstream file read in §1 (branch `concedo`,
commit `f41f621e09822cc6ba48f3d791c41c239ebb6335`, git blob
`e47b699caed03db066575af01006d83067564b59`). The replacement retains the
official one-cell selection/download/load/launch mechanics — including
`%cd /content`, `--model <URL>` handled by KoboldCpp itself, upstream's
`wget` latest-binary line and mirror fallback, `aria2` installation, the
feature command fragments, deletion block, GPU check, Drive handling, and
localtunnel fallback. The narrow changes are the badge/instructions,
four coding/API quick presets and manual model dropdown, context
defaults, `DeleteExistingModels` default OFF, small Dionysus setting
fragments for `--quantkv`, flash attention, batch size, generation limit,
parallel requests, MMQ, web search, remote tunnel, generated password
environment values, and `ExtraArgs`, plus omission of the non-loader
silent-audio cell.

This intentionally supersedes §6's pinned-binary/custom-downloader
choices in order to preserve upstream's working inner code at the owner's
direction. The rebuilt notebook was executed locally in a Jupyter kernel
under the exact fresh-`/content` condition with stubbed
`wget`/`apt`/KoboldCpp commands; the unmodified upstream loader was run
in the same harness, and all four adapted presets plus a manual override
reached the expected fake launch arguments. A real Colab GPU/model/tunnel
run by the owner is still pending, and W-021/Q14 remains open.

## 8. Preset-list correction (later on 2026-10-18)

The owner then objected to editorial preset names such as “Fast smoke
test” and asked for a larger modern list plus the source of the real
KoboldCpp presets. The source is not a separate preset repo: it is the
`Template`/`Model` form variables and `if Template == ...` assignments in
upstream's `colab.ipynb` at the commit/blob above.

The four §7 presets were therefore replaced with **17 plainly named
model + quantization presets** using direct Hugging Face
`resolve/main/.../*.gguf` links in upstream's style. The default is now
`Qwen3.5-9B Q5_K_M`. The full list, file sizes, preset contexts,
Hugging Face sources, 16 GB T4-class fit criteria, and too-large modern
models deliberately excluded are recorded in
[`MODEL_PRESETS.md`](MODEL_PRESETS.md). Only the Template/Model setting
values and preset assignments changed in this correction; the upstream
download/load/launch mechanics retained in §7 were not rewritten. All 17
presets plus the manual override were then re-executed in the local
stubbed Jupyter harness and reached the expected fake launch arguments.
Real Colab downloads/loads for these models remain untested by this
session.

## 9. Streamlining and targeted memory/coder check (later on 2026-10-18)

The owner then noted that the §8 notebook still exposed upstream's
AceStep/music, image-generation, speech-recognition, TTS, vision,
embeddings, and other loaders. At that explicit direction, the adapted
loader was narrowed in place:

- deleted the image-generation, Whisper/speech-recognition, TTS,
  embeddings, AceStep/music, and multiplayer form sections;
- deleted their checked-box/manual-print/start-print handling, command
  construction (`SCommand`, `WCommand`, `TTSCommand`, `ECommand`,
  `MuCommand`, `MPCommand`), and final launch fragments;
- retained exactly one image-reader/OCR path: the
  `Qwen3-VL-8B-Instruct Q6_K` preset and its matched BF16 `mmproj`.
  The manual projector dropdown now offers only that matched file.
  Using it still requires uploading/sending an image; it does not let
  the model watch the owner's screen automatically.

The text-model selection, `--model <URL>`, binary download, GPU check,
Drive/localtunnel utilities, Dionysus setting fragments, password
handling, model-deletion block, and final upstream-style launch flow
were otherwise retained.

A targeted article/community check (not another exhaustive survey)
found the repeated 16 GB-class coding shortlist—Devstral Small 2,
GPT-OSS-20B, and Qwen3-Coder-30B-A3B—already present in §8. Explicit
third-party Colab-memory sources state the important split: a T4 is
marketed as 16 GB VRAM but exposes about 15 GB usable GPU RAM in
Colab, while a standard runtime has roughly 12–13 GB separate system
RAM. Those pools are not unified. The notebook's quick presets set
GPU layers to 999 and remain curated for full-GPU loading; manual
`Layers = Auto` (`--gpulayers -1`) may spill layers into system RAM at
lower speed. Sources and article-specific caveats are recorded in
[`MODEL_PRESETS.md`](MODEL_PRESETS.md).

The streamlined notebook was re-executed locally in the same stubbed
Jupyter harness: the full default notebook, all 17 presets, a manual
text override, and a manual Qwen3-VL image-reader selection reached
the expected fake KoboldCpp launches, with no deleted-feature launch
fragments. Real Colab allocation/download/GPU fit/speed/quality, a
real screenshot test, and W-021/Q14 remain unproven/open.

## 10. Bonsai and the owner's strict reserve rule (later on 2026-10-18)

The owner then asked about the Bonsai model and proposed reserving
1 GB for CUDA, 1 GB for other runtime work, and 1 GB (or more) for
context, with the model required to fit the remainder. Applied in
GiB to about 15 GiB usable Colab GPU RAM, the strict screen is:

```text
model GiB + 1 CUDA/driver + 1 other + max(1, estimated q8 KV) <= 15
```

Three compatible Bonsai presets were added (20 total), all at context
32768:

- `Bonsai-8B Q1_0` — 1.16 GB file; strict estimate about 5.33 GiB
  including its about 2.25 GiB Qwen3-style KV at 32768.
- `Bonsai-27B Q1_0` — 3.8 GB file; strict estimate about 6.54 GiB.
- `Ternary-Bonsai-27B Q2_g64` — 7.59 GB official group-64 pack;
  strict estimate about 10.07 GiB.

The checked KoboldCpp `v1.123.1`/`concedo@f41f621...` source defines
standard `Q1_0` (type 41) and group-64 `Q2_0` (type 42) with CUDA
paths. It does **not** contain `prism_hadamard`, so Bonsai 2 packs
were not added: its `PQ2_0`/`PTQ1_0` types are Prism-private, and its
standard-type `Q2_0` pack still needs the Bonsai 2 Hadamard runtime
and can otherwise load but produce gibberish. The legacy group-128
`Q2_0` file was also avoided in favour of `Q2_g64`.

The same strict arithmetic reclassifies the earlier 13.3–13.5 GB
presets as tight rather than strict-safe; `MODEL_PRESETS.md` records
the exact exception list. All 20 presets, the full default notebook,
the manual text override, and the manual Qwen3-VL path were
re-executed in the stubbed local Jupyter harness. Real Colab loading
of the Q1_0/Q2_0 tensor types, speed, coherence, coding quality, and
tool calling remain unproven.
