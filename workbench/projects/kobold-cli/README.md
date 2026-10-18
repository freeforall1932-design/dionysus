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
> download/load/launch cell, and changes presets/default settings for
> coding/API use. The replacement has been executed locally in a Jupyter
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
2. Leave the quick preset on **Fast smoke test - Qwen2.5-Coder 1.5B** and
   leave the manual loader checkboxes unchecked.
3. Press **Play on the one big code cell**. There is no separate preflight
   cell to run.
4. Wait. Just like the official notebook, the first run downloads the
   current KoboldCpp Linux binary (about 0.65 GB), runs `apt update`,
   installs `aria2`, and then KoboldCpp downloads/loads the selected
   model (about 1 GB for the smoke test). Several minutes before the
   Cloudflare URL appears is normal.
5. Copy the printed **Dionysus API password**. For an API client, use the
   printed tunnel URL plus `/v1` as the base URL and that password as the
   Bearer token/API key.
6. When finished, stop the cell and use **Runtime → Disconnect and delete
   runtime**.

If the run fails, send the last error/output section. Do not paste the API
password into Git or a public issue.

## Exactly what changed from the official notebook

Base file: `LostRuins/koboldcpp/colab.ipynb`, branch `concedo`, commit
`f41f621e09822cc6ba48f3d791c41c239ebb6335`, git blob
`e47b699caed03db066575af01006d83067564b59` (upstream license AGPL-3.0).

The adaptation is intentionally narrow:

- The badge now reopens this Dionysus notebook, and the welcome text gives
  coding/API instructions.
- The 15 upstream quick templates and long roleplay/general model dropdown
  are replaced by four coding/API presets:
  - Qwen2.5-Coder 1.5B Q4_K_M, context 16384 (fast smoke test);
  - Qwen2.5-Coder 7B Q5_K_M, context 32768;
  - Qwen2.5-Coder 14B Q4_K_M, context 32768;
  - Mistral Small 3.2 24B Q4_K_S, context 10240 (tight fit).
  The manual model field still accepts a custom GGUF URL, exactly as
  upstream's manual path does.
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
- construction of `MdCommand`, `VCommand`, `SCommand`, `WCommand`,
  `TTSCommand`, `ECommand`, `MuCommand`, and `MPCommand` for upstream's
  text/vision/image/speech/TTS/embeddings/music/multiplayer options;
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
four preset model URLs themselves are pinned to Hugging Face revisions.
KoboldCpp's remote-tunnel helper remains upstream behaviour.

## Local execution evidence for this replacement

On 2026-10-18, after the owner's real-Colab error report:

- the official notebook was fetched again from GitHub and its loader cell
  was diffed against the adapted loader cell;
- both notebooks passed `nbformat` validation;
- both loader cells compiled after IPython's own input transformation;
- the adapted notebook was executed in a Jupyter kernel with `/content`
  present but **no `/content/kobold-cli`**, a dummy
  `/opt/bin/nvidia-smi` file for upstream's existence check, and stub
  `wget`/`apt`/KoboldCpp commands. It selected the 1.5B preset, reached
  the fake launch, passed `--quantkv q8_0`, batch 512, parallel 1,
  remote tunnel, and set both password environment variables;
- the unmodified upstream loader cell was run in the same harness as a
  baseline and reached its fake launch;
- all four adapted presets and a manual override (custom model URL,
  flash attention off, MMQ off, web search on, generation limit, and an
  extra draft-model argument) were executed the same way and produced
  the expected final arguments.

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
- [COLAB_NOTEBOOK_DISSECTION_2026-10-18.md](COLAB_NOTEBOOK_DISSECTION_2026-10-18.md)
  — primary-source anatomy and flag verdicts, plus a correction note
  recording why the first custom implementation was replaced by this
  upstream-based adaptation.

## Next steps (owner-named, not automatic)

1. Owner opens the rebuilt notebook in Colab and presses Play on the big
   cell with the default 1.5B smoke-test preset; report the tunnel/model
   load result or the exact error.
2. W-021/Q14: verify current Colab free terms, session/usage rules, and
   whether tunnel/API use is acceptable before relying on this endpoint.
3. Record the first successful real run here: GPU, VRAM, model, context,
   load time, tunnel reachability, and an actual tool-calling probe.
