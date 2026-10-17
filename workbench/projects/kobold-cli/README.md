# Kobold CLI (KoboldCpp on Colab)

> **What this folder is for:** the Colab/KoboldCpp arm of the AI team —
> while a Colab session is online, it should act as one pooled,
> password-protected, OpenAI-style API endpoint the council can use; when
> it is offline, the other free APIs carry on. Direction recorded in
> [the AI Team Kit context](../ai-team-kit/PROJECT_CONTEXT.md).
>
> **Status (2026-10-18): owner-directed test notebook added; not yet run
> on Colab.** The notebook defaults to **preflight only** (no download, no
> tunnel). Colab's current terms/limits still need the W-021/Q14 evidence
> pass in [the kit worklist](../ai-team-kit/WORKLIST.md) before this is
> relied on as a pool endpoint.

## Try it

Direct Colab link (also the only content of
[`COLAB_LINK.txt`](COLAB_LINK.txt)):

<https://colab.research.google.com/github/freeforall1932-design/dionysus/blob/arena/5bf33a0c-dionysus/workbench/projects/kobold-cli/kobold-cli.ipynb>

That link intentionally points at this session/PR branch so the owner can
test before merge. After the PR is merged into the default `dionysus`
branch, update `COLAB_LINK.txt`, the badge inside the notebook, and this
README to the `dionysus` branch in one small commit.

First run: choose a GPU runtime, run Cell 1 unchanged, and read the
preflight. Nothing downloads or becomes public until the mode is changed
deliberately in Cell 1 and the later cells are run.

## Contents

- [`kobold-cli.ipynb`](kobold-cli.ipynb) — our small coding-focused
  notebook: four pinned coding-model presets plus custom GGUF URL,
  context, `--quantkv`, flash-attention toggle, GPU layers, batch size,
  generation cap, parallel requests, MMQ toggle, optional manual RoPE,
  guarded extra-args, and an exact-command preview. KoboldCpp `v1.123.1`
  is downloaded from the pinned GitHub release and SHA-256 verified;
  models are pinned to Hugging Face revisions and checked for a GGUF
  header. Launch mode binds to loopback inside the runtime and generates
  a fresh password. No keep-alive cell is included.
- [`COLAB_LINK.txt`](COLAB_LINK.txt) — exactly one line: the direct
  “open this repo notebook in Colab” URL above.
- [COLAB_NOTEBOOK_DISSECTION_2026-10-18.md](COLAB_NOTEBOOK_DISSECTION_2026-10-18.md)
  — what the official notebook really does; approve/reject verdicts on
  another model's “missing flags” claims (flash attention and MMQ turned
  out to be already-on defaults; KV-cache quantization and a generic
  args field are genuinely missing); and the spec this notebook follows.
  One refinement made while building: admin mode stays **off**; the
  generated secret is supplied as both the API password and the admin
  password environment value so a later admin enable cannot start
  unprotected by accident.

## Upstream

- Project: <https://github.com/LostRuins/koboldcpp> (branch `concedo`;
  this notebook pins release `v1.123.1`, tag commit
  `9be8c136ae7e17eb50d9b7a6f3dff5038fcc3186`).
- Official notebook:
  <https://colab.research.google.com/github/LostRuins/koboldcpp/blob/concedo/colab.ipynb>
  (dissected at commit `f41f621e09822cc6ba48f3d791c41c239ebb6335`,
  2026-10-17; the CLI flags used here were rechecked in the `v1.123.1`
  source).
- No upstream notebook code is copied. The notebook is original project
  code that downloads the upstream binary at runtime.
- Known residual: KoboldCpp's `--remotetunnel` downloads Cloudflare's
  `cloudflared` helper from a moving latest-release URL inside upstream
  code. The KoboldCpp binary itself is pinned and hash-checked here.

## Next steps (owner-named, not automatic)

1. Owner runs Cell 1 in preflight mode and reports GPU/output; only then
   decide whether to download/launch the fast 1.5B smoke-test preset.
2. W-021/Q14: verify current Colab free terms, session/usage rules, and
   whether tunnel/API use is acceptable before relying on this endpoint.
3. Record the first real run here: GPU, VRAM, model, context, load time,
   tunnel reachability, and an actual tool-calling probe result.
