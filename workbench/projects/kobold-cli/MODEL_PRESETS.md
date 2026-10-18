# Kobold CLI model presets

> **Checked:** 2026-10-18 against the Hugging Face file trees linked below.
> **Target:** a free Colab T4-class runtime. The T4 is marketed as 16 GB,
> but Colab commonly exposes about 15 GB usable GPU RAM; system RAM is a
> separate roughly 12–13 GB pool (see the memory section below). Quick
> presets are curated for full-GPU loading with this notebook's default
> `KVCache = "q8_0"`, flash attention on, batch size 512, and one
> parallel request.
>
> Preset names are intentionally plain: **model name + quantization**.
> There are no editorial labels such as “fast smoke”, “balanced”, or
> “stronger”.

## Where the real KoboldCpp presets live

The official presets are not in a separate preset repository. They are
variables inside the official notebook file in the KoboldCpp repository:

- Repository: <https://github.com/LostRuins/koboldcpp>
- Official notebook file:
  <https://github.com/LostRuins/koboldcpp/blob/concedo/colab.ipynb>
- Official Colab link:
  <https://colab.research.google.com/github/LostRuins/koboldcpp/blob/concedo/colab.ipynb>
- Branch/commit checked for this adaptation: `concedo` at
  `f41f621e09822cc6ba48f3d791c41c239ebb6335`
- Notebook git blob: `e47b699caed03db066575af01006d83067564b59`

In that notebook's one large code cell, the preset source is the
`Template = ... # @param [...]` dropdown, the manual `Model = ...`
Hugging Face URL dropdown, and the following `if Template == ...`
assignments. The Dionysus notebook retains that structure and the
upstream text-model download/load/launch mechanics; it replaces the
template names, Hugging Face URLs, and preset context assignments with
the list below. At the owner's request, upstream's image-generation,
speech-recognition, TTS, embeddings, AceStep/music, and multiplayer
form sections and launch fragments have been deleted. The one retained
non-text loader path is Qwen3-VL's matching `--mmproj`, used as the
image-reader/OCR path.

Like the official notebook, these entries use direct Hugging Face
`resolve/main/.../*.gguf` links. KoboldCpp receives the selected URL as
`--model <URL>` and handles the model download/load itself. Because
`main` can move, re-check the linked Hugging Face file tree if a future
download returns 404.

## Presets now in `kobold-cli.ipynb`

“GGUF file” is the selected model file only. It does not include the
KoboldCpp binary (about 0.65 GB of disk, not VRAM), KV cache, compute
buffers, or the Qwen3-VL projector where separately noted. File sizes are
the decimal GB shown by Hugging Face.

| Preset name in the notebook | GGUF file | Preset context | Type / note | Hugging Face source |
|---|---:|---:|---|---|
| `Qwen3.5-9B Q5_K_M` | 6.58 GB | 32768 | Default; current Qwen3.5 dense model, text preset | [unsloth/Qwen3.5-9B-GGUF](https://huggingface.co/unsloth/Qwen3.5-9B-GGUF/tree/main) |
| `Qwen3.5-4B Q4_K_M` | 2.74 GB | 32768 | Smaller current Qwen3.5 model, text preset | [unsloth/Qwen3.5-4B-GGUF](https://huggingface.co/unsloth/Qwen3.5-4B-GGUF/tree/main) |
| `Qwen3.5-27B Q3_K_M` | 13.5 GB | 16384 | Larger Qwen3.5 dense model; Q3 is a quality trade-off | [unsloth/Qwen3.5-27B-GGUF](https://huggingface.co/unsloth/Qwen3.5-27B-GGUF/tree/main) |
| `Qwen3-8B Q5_K_M` | 5.85 GB | 32768 | Qwen3 general/reasoning model | [Qwen/Qwen3-8B-GGUF](https://huggingface.co/Qwen/Qwen3-8B-GGUF/tree/main) |
| `Qwen3-14B Q5_K_M` | 10.5 GB | 32768 | Larger Qwen3 general/reasoning model | [Qwen/Qwen3-14B-GGUF](https://huggingface.co/Qwen/Qwen3-14B-GGUF/tree/main) |
| `Qwen2.5-Coder-7B Q5_K_M` | 5.44 GB | 32768 | Established coding-specialist model | [Qwen/Qwen2.5-Coder-7B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-Coder-7B-Instruct-GGUF/tree/main) |
| `Qwen2.5-Coder-14B Q4_K_M` | 8.99 GB | 32768 | Established larger coding-specialist model | [Qwen/Qwen2.5-Coder-14B-Instruct-GGUF](https://huggingface.co/Qwen/Qwen2.5-Coder-14B-Instruct-GGUF/tree/main) |
| `Qwen3-Coder-30B-A3B UD-IQ3_XXS` | 12.85 GB | 8192 | Current coding MoE in a smaller dynamic quant so the 30B file can fit | [unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF](https://huggingface.co/unsloth/Qwen3-Coder-30B-A3B-Instruct-GGUF/tree/main) |
| `Devstral-Small-2-24B Q4_K_S` | 13.5 GB | 8192 | Current Mistral coding model; smaller Q4 variant for T4 headroom | [unsloth/Devstral-Small-2-24B-Instruct-2512-GGUF](https://huggingface.co/unsloth/Devstral-Small-2-24B-Instruct-2512-GGUF/tree/main) |
| `Ministral-3-8B-Instruct-2512 Q4_K_M` | 5.20 GB | 32768 | Current Mistral instruct model, text preset | [mistralai/Ministral-3-8B-Instruct-2512-GGUF](https://huggingface.co/mistralai/Ministral-3-8B-Instruct-2512-GGUF/tree/main) |
| `Ministral-3-14B-Instruct-2512 Q4_K_M` | 8.24 GB | 32768 | Larger Ministral 3 instruct model, text preset | [mistralai/Ministral-3-14B-Instruct-2512-GGUF](https://huggingface.co/mistralai/Ministral-3-14B-Instruct-2512-GGUF/tree/main) |
| `Mistral-Small-3.2-24B Q4_K_S` | 13.5 GB | 10240 | Same model family/quant size class as an official Kobold template | [unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF](https://huggingface.co/unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF/tree/main) |
| `GPT-OSS-20B MXFP4` | 12.1 GB | 32768 | OpenAI open-weight MoE; also represented in the official Kobold templates | [ggml-org/gpt-oss-20b-GGUF](https://huggingface.co/ggml-org/gpt-oss-20b-GGUF/tree/main) |
| `Gemma-4-E4B-it Q4_K_M` | 4.98 GB | 32768 | Stock Google Gemma 4 E4B instruct GGUF, text preset | [unsloth/gemma-4-E4B-it-GGUF](https://huggingface.co/unsloth/gemma-4-E4B-it-GGUF/tree/main) |
| `Qwen3-VL-8B-Instruct Q6_K` | 6.73 GB + 1.16 GB `mmproj-BF16.gguf` | 32768 | Sole image-reader/OCR preset; the template also sets the matching projector. Upload/send a screenshot or image; it cannot view your screen automatically | [unsloth/Qwen3-VL-8B-Instruct-GGUF](https://huggingface.co/unsloth/Qwen3-VL-8B-Instruct-GGUF/tree/main) |
| `GLM-4.7-Flash Q3_K_S` | 13.3 GB | 8192 | Current GLM coding/agent MoE in a smaller quant for T4 headroom | [unsloth/GLM-4.7-Flash-GGUF](https://huggingface.co/unsloth/GLM-4.7-Flash-GGUF/tree/main) |
| `Phi-4 Q4_K` | 9.05 GB | 16384 | Microsoft Phi-4 reasoning/coding model; preset stays at its 16K context class | [microsoft/phi-4-gguf](https://huggingface.co/microsoft/phi-4-gguf/tree/main) |
| `Bonsai-8B Q1_0` | 1.16 GB | 32768 | PrismML 1-bit Qwen3-8B in the standard `Q1_0` GGUF pack; strict-reserve estimate about 5.33 GiB total (see Bonsai section) | [prism-ml/Bonsai-8B-gguf](https://huggingface.co/prism-ml/Bonsai-8B-gguf/tree/main) |
| `Bonsai-27B Q1_0` | 3.8 GB | 32768 | PrismML 1-bit Qwen3.6-27B hybrid-attention model in the standard `Q1_0` pack; strict-reserve estimate about 6.54 GiB total | [prism-ml/Bonsai-27B-gguf](https://huggingface.co/prism-ml/Bonsai-27B-gguf/tree/main) |
| `Ternary-Bonsai-27B Q2_g64` | 7.59 GB | 32768 | PrismML ternary Qwen3.6-27B in the official group-64 `Q2_0` pack; strict-reserve estimate about 10.07 GiB total | [prism-ml/Ternary-Bonsai-27B-gguf](https://huggingface.co/prism-ml/Ternary-Bonsai-27B-gguf/tree/main) |

## Bonsai additions and the owner's strict reserve rule

The owner proposed a stricter back-of-the-envelope full-GPU rule:
reserve **1 GiB for CUDA/driver**, **1 GiB for other runtime/compute
buffers**, and **at least 1 GiB for KV/context — more for longer
context**. The model weights must fit what remains:

```text
strict total (GiB) = model-file GiB + 1.00 CUDA/driver
                   + 1.00 other runtime/compute
                   + max(1.00, estimated q8_0 KV/context GiB)
                   <= about 15.0 GiB usable GPU RAM
```

If the KV/context estimate is no more than 1 GiB, that means the model
file itself must be about **12.0 GiB or less** (about 12.9 decimal GB
as displayed by Hugging Face). Longer context lowers the weight
allowance further. The added Bonsai rows pass this stricter screen:

- **Bonsai-8B Q1_0:** 1.16 GB file = about 1.08 GiB. Its 36-layer,
  8-KV-head, 128-head-dimension layout needs about 2.25 GiB of
  `q8_0` KV at the preset 32768 context, so the strict estimate is
  about **1.08 + 1 + 1 + 2.25 = 5.33 GiB**.
- **Bonsai-27B Q1_0:** 3.8 GB file = about 3.54 GiB. Only 16 of its
  64 hybrid-attention layers grow a full-attention KV cache; at 32768
  that full-attention KV is about 1.0 GiB at `q8_0`, giving about
  **3.54 + 1 + 1 + 1.0 = 6.54 GiB** (linear-attention state and other
  work buffers are part of why the separate 1 GiB “other” reserve is
  kept).
- **Ternary-Bonsai-27B Q2_g64:** 7.59 GB file = about 7.07 GiB, so
  about **7.07 + 1 + 1 + 1.0 = 10.07 GiB** at 32768.

Compatibility mattered as much as size. The checked KoboldCpp source
(`v1.123.1` / `concedo@f41f621...`) defines standard GGML `Q1_0`
(type 41, group 128) and `Q2_0` (type 42, **group 64**) and contains
CUDA dequantization/MMQ paths for both:
<https://github.com/LostRuins/koboldcpp/blob/concedo/ggml/include/ggml.h>
and
<https://github.com/LostRuins/koboldcpp/blob/concedo/ggml/src/ggml-common.h>.
That is why the notebook uses `Bonsai-*-Q1_0.gguf` and
`Ternary-Bonsai-27B-Q2_g64.gguf`, **not** the similarly named legacy
group-128 `Q2_0` file or a `PQ2_0` file. PrismML's troubleshooting
page likewise warns that legacy no-`g64` ternary files use the wrong
layout for current binaries and that `PQ2_0` needs PrismML's fork:
<https://docs.prismml.com/resources/troubleshooting>.

**Bonsai 2 is deliberately not a preset yet.** Its smaller
`PTQ1_0`/`PQ2_0` packs use Prism-private GGML types, and even its
standard-type `Q2_0` pack needs Bonsai 2's Hadamard activation
runtime; PrismML says a runtime that knows only the tensor type can
load it and produce gibberish
(<https://docs.prismml.com/download/formats>). The checked KoboldCpp
source does not yet contain `prism_hadamard`, so adding Bonsai 2 now
could silently produce bad output rather than fail cleanly. Revisit
it only after KoboldCpp syncs that runtime support.

Fit is not the same as coding quality. PrismML's card reports strong
benchmarks, but community/reviewer reports are mixed—especially for
Bonsai-8B code generation—so these rows are added because their
footprint/context arithmetic is unusually safe, not because this
session proved they beat Devstral, GPT-OSS, or Qwen3-Coder. Real
Colab speed, coherence, tool calling, and code quality still need an
owner run.

Under the same strict screen, four earlier rows do **not** pass even
before replacing the 1 GiB context minimum with a larger actual KV
estimate: `Qwen3.5-27B Q3_K_M`, `Devstral-Small-2-24B Q4_K_S`, and
`Mistral-Small-3.2-24B Q4_K_S` are about 12.57 GiB of weights
(15.57 GiB after the minimum 3 GiB reserve), and
`GLM-4.7-Flash Q3_K_S` is about 12.39 GiB (15.39 GiB after reserves).
They remain available, but should now be read as **tight presets**:
they may still load when the real CUDA/other/KV usage is below these
conservative reserves, otherwise use manual `Layers = Auto` and/or a
lower context. `Qwen3-Coder-30B-A3B UD-IQ3_XXS` (about 14.97 GiB with
the minimum reserve) and `GPT-OSS-20B MXFP4` (about 14.27 GiB) are
borderline under the same arithmetic once longer-context KV is taken
into account.

## Targeted article/community coding shortlist

At the owner's request, this was a targeted article/community check,
not another exhaustive model survey. The repeated 16 GB-class coding
shortlist is already in the dropdown:

- [LocalAI Master’s 16 GB coding guide](https://localaimaster.com/vram/best-coding-llm-16gb-vram)
  names **Devstral Small 2 24B** its winner, while warning that about
  15 GB at `Q4_K_M` is a tight fit. This notebook uses the smaller
  13.5 GB `Q4_K_S` file at context 8192.
- [ZimaSpace’s by-VRAM coding table](https://shop.zimaspace.com/blogs/tech-ai-hub/best-local-coding-models-8gb-12gb-16gb-24gb-vram)
  likewise starts the 16 GB tier with Devstral Small 2 and lists
  **Qwen3-Coder-30B-A3B** as the coding specialist in a 3-bit-class
  quant. This notebook uses `UD-IQ3_XXS` at context 8192.
- [TechFuelHQ’s task test](https://techfuelhq.com/articles/best-local-llm-coding-2026/)
  gives its 16 GB pick to **GPT-OSS-20B** because it passed its eight
  tasks while fully GPU-resident, and treats Qwen3-Coder-30B as the
  quality-ceiling/partially-resident alternative. This notebook uses
  GPT-OSS `MXFP4`.
- A [r/LocalLLM Devstral/Qwen quant release](https://www.reddit.com/r/LocalLLM/comments/1r9xifw/devstral_small_2_24b_qwen3_coder_30b_quants_for/)
  reports low-3-bit builds fitting a 16 GB GPU at 32K context. The
  notebook nevertheless keeps its Devstral and Qwen3-Coder presets at
  8192 because free Colab exposes roughly 15 GB usable GPU RAM and only
  roughly 12–13 GB system RAM, not a desktop 16 GB card beside a large
  system-RAM pool.

The default remains `Qwen3.5-9B Q5_K_M` for the first end-to-end run;
that is not a claim that it out-codes Devstral, GPT-OSS, Qwen3-Coder,
or the Bonsai additions. Coding quality and speed on a real Colab T4
still need an owner run.

## Colab memory: GPU VRAM and system RAM are separate

- NVIDIA's T4 specification lists **16 GB GDDR6** GPU memory:
  <https://www.nvidia.com/en-us/data-center/tesla-t4/>.
- A 2026 free-tier guide explicitly says Colab's T4 has 16 GB VRAM
  (**about 15 GB usable after ECC**) and **roughly 12–13 GB of system
  RAM**: <https://aicreditmart.com/ai-credits-providers/google-colab-free-tier-t4-gpu-access-guide-2026/>.
  Another Colab resource summary gives the same split more precisely
  as about **15 GB GPU RAM + 12.7 GB system RAM**:
  <https://productishand03.substack.com/p/google-colab-free-high-value-resource>.
  These are third-party observations, not a Google guarantee; check
  the resource monitor on the actual runtime.
- The arithmetic total is therefore roughly 27–28 GB, but it is **not
  one unified pool**. A fully GPU-offloaded model still needs its
  weights, KV cache, and compute buffers to fit usable GPU RAM.
- KoboldCpp can split layers between GPU and system RAM. Its wiki says
  `--gpulayers -1` enables autofit/guessing
  (<https://github.com/LostRuins/koboldcpp/wiki>), and the Quicklaunch
  guide explains that GPU layers are generally faster while the rest
  remain in system RAM
  (<https://koboldai.com/Guides/Kobold_CPP/KoboldCpp_Quicklaunch/>).
- This notebook's quick templates follow upstream and set GPU layers
  to 999, so system RAM does **not** rescue an oversized quick preset.
  Manual `Layers = Auto` becomes `--gpulayers -1` and may spill some
  weights to system RAM, but the CPU-side weights plus Python,
  KoboldCpp, buffers, and cache still have to fit roughly 12–13 GB,
  and CPU-held layers are slower.
- Therefore, desktop articles that say “runs on 16 GB” while assuming
  32–64 GB of system RAM for spill cannot be copied directly onto
  free Colab.

## How “fit” was judged

- Every preset is one direct, non-split GGUF file (the vision preset is
  one model file plus its separate projector, using upstream's existing
  `CustomMmproj` path).
- The original list used a looser first-pass screen (largest files
  about 13.5 GB / 12.6 GiB). The owner's stricter reserve rule above
  now supersedes any broad claim that every row is strict-safe: use
  model GiB + 1 GiB CUDA/driver + 1 GiB other + at least 1 GiB (or the
  actual longer-context KV estimate) against about 15 GiB usable.
  The Bonsai additions pass; the four 13.3–13.5 GB rows named above
  are tight/manual-fallback candidates under that stricter rule.
  Every figure remains an estimate from file size and architecture,
  not a guarantee for every Colab allocation or future KoboldCpp
  build.
- Quick templates follow upstream behaviour and set GPU layers to 999.
  If a large preset runs out of VRAM on a particular runtime, use the
  manual path instead: check `LoadTextModel`, choose the same model URL,
  set `Layers` to `Auto`, and lower `ContextSize`. `Auto` may spill
  layers into the separate system-RAM pool, normally more slowly.
- The deleted extra model sections mean no second image-generation,
  speech, TTS, embeddings, or music model shares VRAM with the selected
  text model. The Qwen3-VL projector is included in that preset's
  budget above.
- `DeleteExistingModels` defaults OFF. Trying several presets in one
  runtime can fill `/content` disk even when each model fits VRAM one at
  a time; disconnect/delete the runtime between large downloads if disk
  space becomes an issue.

## Modern models deliberately not made quick presets

These are not quick presets because their commonly recommended GGUF
files are too large for the same full-GPU Colab target (roughly 15 GB
usable), even though some can be attempted manually with partial
offload into the roughly 12–13 GB system-RAM pool, a lower quant, or a
larger GPU:

- **Qwen3-Coder-Next (80B A3B):** useful quants are tens of GB.
- **Qwen3-Coder-30B-A3B Q4_K_M:** about 18.6 GB before KV/buffers. The
  preset above uses `UD-IQ3_XXS` instead.
- **GLM-4.7-Flash Q4_K_M:** about 18.3 GB before KV/buffers. The preset
  above uses `Q3_K_S` instead.
- **Qwen3.5-27B Q4_K_M:** about 16.7 GB before KV/buffers. The preset
  above uses `Q3_K_M` instead.
- **Qwen3.5-35B-A3B Q4_K_M:** about 22 GB before KV/buffers.
- **32B-class dense Q4 models:** generally about 19–20 GB before
  KV/buffers.
- **Qwen3.6-35B-A3B Q4-class builds:** one newer roundup recommends
  this family for constrained hardware with RAM offload
  (<https://insiderllm.com/guides/best-local-coding-models-2026/>), but
  that is not this notebook's full-GPU quick-preset target and no
  successful free-Colab load was proven in this check.
- **Ternary Bonsai 2:** excluded for runtime compatibility, not size.
  Its files would pass the strict memory screen, but the checked
  KoboldCpp build does not yet contain Bonsai 2's Hadamard runtime;
  see the Bonsai section above.

## Tested / not tested for this preset update

- **Checked:** each Hugging Face repository/file name and displayed file
  size on 2026-10-18, including the three Bonsai blob pages; the
  targeted coding-shortlist, Colab-memory, Bonsai-format, and
  KoboldCpp-source checks above; notebook JSON/`nbformat`; the
  streamlined loader's Python syntax after IPython transformation;
  local Jupyter execution of the full default notebook, all 20
  presets, a manual text override, and a manual Qwen3-VL
  image-reader selection with stubbed `wget`/`apt`/KoboldCpp
  commands. Each reached the expected `--model`, context, and (for
  Qwen3-VL) `--mmproj` arguments, and none emitted a deleted
  image-generation/speech/TTS/embeddings/music/multiplayer launch
  fragment.
- **Not tested here:** downloading every real model in Colab, loading
  every architecture (including the new Q1_0/Q2_0 Bonsai tensor types)
  on a real T4, generation speed, output quality/coherence,
  tool-calling quality, or tunnel/API behaviour. The sandbox cannot use
  the owner's Google account or allocate the owner's Colab GPU. A model
  being listed means its file/context budget was curated for the target,
  not that this session proved a successful Colab load.
