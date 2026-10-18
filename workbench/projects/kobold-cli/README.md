# Kobold CLI (KoboldCpp on Colab)

> **What this folder is for:** the Colab/KoboldCpp arm of the AI team —
> while a Colab session is online, it should act as one pooled,
> password-protected, OpenAI-style API endpoint the council can use; when
> it is offline, the other free APIs carry on. Direction recorded in
> [the AI Team Kit context](../ai-team-kit/PROJECT_CONTEXT.md).
>
> **Status (2026-10-18): rebuilt from the official KoboldCpp notebook
> after the owner reported that the first custom notebook failed in real
> Colab.** The first version called `shutil.disk_usage()` on
> `/content/kobold-cli` before creating that folder. The replacement does
> not use that custom folder or custom downloader at all: it starts from
> upstream's actual `colab.ipynb`, retains upstream's working
> text-model download/load/launch cell, and changes presets/default
> settings for coding/API use. It has since been streamlined at the
> owner's request: unrelated extra model sections are deleted, leaving
> text/coding models plus one Qwen3-VL image-reader/OCR path. The replacement has been executed locally in a Jupyter
> kernel with stubbed download/binary commands, but it has **not yet been
> owner-run in a real Colab GPU runtime**. W-021/Q14 terms evidence is
> still open.

## Try it

Direct Colab link (also the only content of
[`COLAB_LINK.txt`](COLAB_LINK.txt)):

<https://colab.research.google.com/github/freeforall1932-design/dionysus/blob/arena/5bf33a0c-dionysus/workbench/projects/kobold-cli/kobold-cli.ipynb>

That link intentionally points at this session/PR branch so the owner can
test before merge. After the PR is merged into the default `dionysus`
branch, update `COLAB_LINK.txt`, the badge inside the notebook, and this
README to the `dionysus` branch in one small commit.

### First run

1. Open the link and choose a GPU runtime if Colab does not already offer
   one.
2. Leave the quick preset on **Qwen3.5-9B Q5_K_M** and
   leave the manual loader checkboxes unchecked. Preset names are plain
   model name + quantization; the full 20-entry list is in
   [`MODEL_PRESETS.md`](MODEL_PRESETS.md).
3. Press **Play on the one big code cell**. There is no separate preflight
   cell to run.
4. Wait. Just like the official notebook, the first run downloads the
   current KoboldCpp Linux binary (about 0.65 GB), runs `apt update`,
   installs `aria2`, and then KoboldCpp downloads/loads the selected
   model (about 6.6 GB for the default preset). Several minutes before the
   Cloudflare URL appears is normal.
5. Copy the printed **Dionysus API password**. For an API client, use the
   printed tunnel URL plus `/v1` as the base URL and that password as the
   Bearer token/API key.
6. When finished, stop the cell and use **Runtime → Disconnect and delete
   runtime**.

If the run fails, send the last error/output section. Do not paste the API
password into Git or a public issue.

### Screenshot / image-reader run

To let the model read an app screenshot or perform OCR:

1. Restart the big cell with the quick preset set to
   **Qwen3-VL-8B-Instruct Q6_K** and leave the manual checkboxes
   unchecked. That preset loads the matched model and image projector
   together.
2. Open the KoboldCpp tunnel URL.
3. Upload/send the screenshot or image and ask what text/UI state it
   shows.

The model cannot see your screen automatically; you have to supply the
image. Avoid uploading screenshots containing passwords, private keys,
or other sensitive information to a temporary tunnel.

## Exactly what changed from the official notebook

Base file: `LostRuins/koboldcpp/colab.ipynb`, branch `concedo`, commit
`f41f621e09822cc6ba48f3d791c41c239ebb6335`, git blob
`e47b699caed03db066575af01006d83067564b59` (upstream license AGPL-3.0).

The adaptation is intentionally narrow:

- The badge now reopens this Dionysus notebook, and the welcome text gives
  coding/API instructions.
- The 15 upstream quick templates and long roleplay/general model dropdown
  are replaced by 20 plainly named presets (**model name + quantization
  only**) for a free-Colab T4-class runtime (about 15 GB usable VRAM)
  in [`MODEL_PRESETS.md`](MODEL_PRESETS.md). They span current Qwen3.5,
  Qwen3, Qwen2.5-Coder, Qwen3-Coder, Devstral, Ministral 3, Mistral Small,
  GPT-OSS, Gemma 4, Qwen3-VL, GLM-4.7-Flash, Phi-4, Bonsai, and
  Ternary-Bonsai GGUF files. The
  manual model field still accepts a custom GGUF URL, exactly as
  upstream's manual path does.
- Upstream's image-generation, speech-recognition, TTS, embeddings,
  AceStep/music, and multiplayer form sections, command-construction
  blocks, and final launch fragments are deleted. The only retained
  non-text loader path is the Qwen3-VL image reader/OCR: one quick
  preset plus one matched manual projector choice.
- Manual context defaults to 16384 and offers larger sizes.
- `DeleteExistingModels` defaults **OFF** instead of upstream's ON, so a
  model already in `/content` during the same runtime is reused.
- A **Dionysus coding/API settings** section adds `KVCache` (default
  `q8_0`), flash-attention on/off, batch size, generation limit, parallel
  requests, MMQ on/off, web-search on/off, remote-tunnel on/off,
  generated-password on/off, and free-form `ExtraArgs`.
- Those settings become small command fragments in upstream's existing
  style (`KCommand`, `FACommand`, and so on). The final launch line is the
  upstream line with those fragments substituted/appended.
- When password generation is on (the default), the cell sets
  `KCPP_PASSWORD` and `KCPP_ADMINPASSWORD` in the environment before the
  upstream launch line and prints the password once. Turning it off
  removes those environment values and returns to upstream's unpassworded
  behaviour, with a warning.
- The upstream silent-audio keep-alive cell is omitted. It is not part of
  model downloading or loading.

## Upstream mechanics deliberately retained

The following are not rewritten:

- the one-big-cell form/selection flow, including quick-template versus
  manual-checkbox override logic (only the template assignments changed);
- the `/opt/bin/nvidia-smi` GPU-presence check;
- optional Google Drive save handling;
- `%cd /content` (Colab already provides `/content`; no custom
  `/content/kobold-cli` directory is needed);
- construction of `MdCommand` for the text model and `VCommand` for
  the retained Qwen3-VL image-reader projector;
- the existing model-deletion block (only its default changed);
- upstream's binary download line, including latest-release URL and
  mirror fallback;
- `chmod +x`, `apt update`, and `apt install aria2 -y`;
- the localtunnel fallback block;
- KoboldCpp receiving the model URL itself (`--model <URL>`) and handling
  the model download/load, as in the official notebook.

Because the owner asked for upstream's working inner code to stay intact,
this adaptation also retains upstream's **unpinned latest-binary
download without a notebook-level hash check**. That is a deliberate
trade-off in this rebuild, not a claim that pinning would be worse. The
preset model URLs also follow upstream's style: direct Hugging Face
`resolve/main/.../*.gguf` links, checked against the file trees on
2026-10-18 and listed in `MODEL_PRESETS.md`. KoboldCpp's remote-tunnel
helper remains upstream behaviour.

## Targeted coding-shortlist and memory check

The articles/community posts checked for this streamlining repeatedly
shortlist **Devstral Small 2 24B**, **GPT-OSS-20B**, and
**Qwen3-Coder-30B-A3B** for 16 GB-class coding; all three were already
presets. The evidence and exact fit caveats are in
[`MODEL_PRESETS.md`](MODEL_PRESETS.md).

The important Colab correction is that “16 GB” is not the whole
machine, but it is also not one pooled memory budget. A T4 is marketed
at 16 GB VRAM, Colab commonly exposes about 15 GB usable GPU RAM, and
a standard runtime has roughly 12–13 GB separate system RAM. Quick
presets set GPU layers to 999 and are therefore aimed at full-GPU
loading. Manual `Layers = Auto` can spill some layers into system RAM
at lower speed, but both pools still have to hold their own portions
plus runtime overhead.

For the owner's stricter screen, count it as **model GiB + 1 GiB
CUDA/driver + 1 GiB other runtime/compute + at least 1 GiB
KV/context (more for longer context) <= about 15 GiB usable**. That
leaves roughly 12 GiB for weights before longer-context KV. The three
added Bonsai presets pass with slack: Bonsai-8B `Q1_0` is about
5.33 GiB strict-estimated at 32768, Bonsai-27B `Q1_0` about
6.54 GiB, and Ternary-Bonsai-27B `Q2_g64` about 10.07 GiB. The
checked KoboldCpp source has standard `Q1_0` and group-64 `Q2_0`
CUDA paths; Bonsai 2 special packs are **not** included because that
build does not yet contain Bonsai 2's Hadamard runtime. Under this
stricter arithmetic, the earlier 13.3–13.5 GB presets are tight
rather than strict-safe; use manual `Auto`/lower context if one
reports OOM. Arithmetic details are in `MODEL_PRESETS.md`.

## Local execution evidence for this replacement

On 2026-10-18, after the owner's real-Colab error report:

- the official notebook was fetched again from GitHub and its loader cell
  was diffed against the adapted loader cell;
- both notebooks passed `nbformat` validation;
- both loader cells compiled after IPython's own input transformation;
- the adapted notebook was executed in a Jupyter kernel with `/content`
  present but **no `/content/kobold-cli`**, a dummy
  `/opt/bin/nvidia-smi` file for upstream's existence check, and stub
  `wget`/`apt`/KoboldCpp commands. In the current preset list it selected
  `Qwen3.5-9B Q5_K_M`, reached the fake launch, passed `--quantkv q8_0`,
  batch 512, parallel 1, remote tunnel, and set both password
  environment variables;
- the unmodified upstream loader cell was run in the same harness as a
  baseline and reached its fake launch;
- after streamlining and the Bonsai update, all 20 adapted presets, a manual override
  (custom model URL, flash attention off, MMQ off, web search on,
  generation limit, and an extra draft-model argument), and a manual
  Qwen3-VL image-reader selection were executed the same way and
  produced the expected final model/context/projector arguments. The
  fake launches contained none of the deleted
  image-generation/speech/TTS/embeddings/music/multiplayer fragments.
  The preset file names and sizes were checked in the linked Hugging
  Face trees in `MODEL_PRESETS.md`.

That is real execution of the notebook logic, but it is **not** a real
Colab run: the sandbox cannot allocate the owner's Colab GPU or use the
owner's Google account. Actual binary/model downloads, GPU fit, tunnel
reachability, and API/tool-calling behaviour still require the owner's
Colab run.

## Contents

- [`kobold-cli.ipynb`](kobold-cli.ipynb) — the adapted official notebook
  (badge, instructions, one upstream loader/launch cell with the settings
  changes above).
- [`COLAB_LINK.txt`](COLAB_LINK.txt) — exactly one line: the direct
  “open this repo notebook in Colab” URL.
- [`MODEL_PRESETS.md`](MODEL_PRESETS.md) — where the official KoboldCpp
  preset source lives, plus the curated 20-model Hugging Face list,
  file sizes, preset contexts, targeted article/community coding
  shortlist, explicit Colab VRAM/system-RAM findings, fit criteria, and
  excluded too-large modern models.
- [COLAB_NOTEBOOK_DISSECTION_2026-10-18.md](COLAB_NOTEBOOK_DISSECTION_2026-10-18.md)
  — primary-source anatomy and flag verdicts, plus a correction note
  recording why the first custom implementation was replaced by this
  upstream-based adaptation.

## Next steps (owner-named, not automatic)

1. Owner opens the rebuilt notebook in Colab and presses Play on the big
   cell with the default `Qwen3.5-9B Q5_K_M` preset; report the
   tunnel/model load result or the exact error.
2. After that first proof, owner can compare one shortlisted coding
   preset (Devstral, GPT-OSS, or Qwen3-Coder), optionally try a Bonsai
   preset for its much smaller strict-memory footprint, and optionally
   test Qwen3-VL with a non-sensitive app screenshot.
3. W-021/Q14: verify current Colab free terms, session/usage rules, and
   whether tunnel/API use is acceptable before relying on this endpoint.
4. Record the first successful real run here: GPU, VRAM, model, context,
   load time, tunnel reachability, and an actual tool-calling probe.
