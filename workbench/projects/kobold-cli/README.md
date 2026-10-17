# Kobold CLI (KoboldCpp on Colab)

> **What this folder is for:** the Colab/KoboldCpp arm of the AI team —
> while a Colab session is online, it should act as one pooled,
> password-protected, OpenAI-style API endpoint the council can use; when
> it is offline, the other free APIs carry on. Direction recorded in
> [the AI Team Kit context](../ai-team-kit/PROJECT_CONTEXT.md).
>
> **Status (2026-10-18): research only.** The official notebook has been
> read and checked line-by-line; nothing has been run on Colab yet, and
> Colab's current terms/limits still need the W-021/Q14 evidence pass in
> [the kit worklist](../ai-team-kit/WORKLIST.md) before real use.

## Contents

- [COLAB_NOTEBOOK_DISSECTION_2026-10-18.md](COLAB_NOTEBOOK_DISSECTION_2026-10-18.md)
  — what the official notebook really does; approve/reject verdicts on
  another model's "missing flags" claims (flash attention and MMQ turned
  out to be already-on defaults; KV-cache quantization and a generic
  args field are genuinely missing); and the spec for our fine-tuned
  form (coding presets, `--quantkv`, password, extra-args, pinned +
  hash-checked binary).

## Upstream

- Project: <https://github.com/LostRuins/koboldcpp> (branch `concedo`).
- Official notebook:
  <https://colab.research.google.com/github/LostRuins/koboldcpp/blob/concedo/colab.ipynb>
  (dissected at commit `f41f621e09822cc6ba48f3d791c41c239ebb6335`,
  2026-10-17).
- Nothing from upstream is copied into this repo yet. If we build the
  fine-tuned notebook, it will be our own small form modelled on the
  spec, credential-free, with the binary version pinned and hash-checked
  at download time.

## Next steps (owner-named, not automatic)

1. W-021/Q14: verify current Colab free terms, session/usage rules, and
   whether tunnel/API use and keep-alive tricks are acceptable.
2. Only then: build the fine-tuned notebook from the spec, run one real
   session, and record GPU, VRAM, speeds, and tool-calling results here.
