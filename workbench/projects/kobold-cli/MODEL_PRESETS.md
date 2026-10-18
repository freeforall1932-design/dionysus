# Kobold CLI model presets

> **Checked:** 2026-10-18 against the Hugging Face file trees linked below.
> **Target:** a free Colab T4-class runtime with about 16 GB VRAM, this
> notebook's default `KVCache = "q8_0"`, flash attention on, batch size
> 512, one parallel request, and no extra image/speech/TTS model loaded.
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
upstream download/load/launch mechanics; it replaces the template names,
Hugging Face URLs, and preset context assignments with the list below.

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
| `Qwen3-VL-8B-Instruct Q6_K` | 6.73 GB + 1.16 GB `mmproj-BF16.gguf` | 32768 | Vision preset; the template also sets the matching projector, as upstream does | [unsloth/Qwen3-VL-8B-Instruct-GGUF](https://huggingface.co/unsloth/Qwen3-VL-8B-Instruct-GGUF/tree/main) |
| `GLM-4.7-Flash Q3_K_S` | 13.3 GB | 8192 | Current GLM coding/agent MoE in a smaller quant for T4 headroom | [unsloth/GLM-4.7-Flash-GGUF](https://huggingface.co/unsloth/GLM-4.7-Flash-GGUF/tree/main) |
| `Phi-4 Q4_K` | 9.05 GB | 16384 | Microsoft Phi-4 reasoning/coding model; preset stays at its 16K context class | [microsoft/phi-4-gguf](https://huggingface.co/microsoft/phi-4-gguf/tree/main) |

## How “fit” was judged

- Every preset is one direct, non-split GGUF file (the vision preset is
  one model file plus its separate projector, using upstream's existing
  `CustomMmproj` path).
- The largest model files were kept to about **13.5 GB or below**, leaving
  room for the preset context's `q8_0` KV cache and runtime buffers in a
  16 GB-class GPU. This is an estimate from file size and architecture,
  not a guarantee for every Colab allocation or future KoboldCpp build.
- Quick templates follow upstream behaviour and set GPU layers to 999.
  If a large preset runs out of VRAM on a particular runtime, use the
  manual path instead: check `LoadTextModel`, choose the same model URL,
  set `Layers` to `Auto`, and lower `ContextSize`.
- Loading an additional image, speech, TTS, embeddings, or music model at
  the same time can push any large text preset out of VRAM.
- `DeleteExistingModels` defaults OFF. Trying several presets in one
  runtime can fill `/content` disk even when each model fits VRAM one at
  a time; disconnect/delete the runtime between large downloads if disk
  space becomes an issue.

## Modern models deliberately not made quick presets

These are not quick presets because their commonly recommended GGUF
files are too large for the same full-offload T4 target, even though some
can be attempted manually with partial offload, a lower quant, or a
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

## Tested / not tested for this preset update

- **Checked:** each Hugging Face repository/file name and displayed file
  size on 2026-10-18; notebook JSON/`nbformat`; the adapted loader's
  Python syntax after IPython transformation; local Jupyter execution of
  every preset and a manual override with stubbed
  `wget`/`apt`/KoboldCpp commands, confirming that each template reaches
  the expected `--model`, context, and projector arguments.
- **Not tested here:** downloading every real model in Colab, loading
  every architecture on a real T4, generation speed, output quality,
  tool-calling quality, or tunnel/API behaviour. The sandbox cannot use
  the owner's Google account or allocate the owner's Colab GPU. A model
  being listed means its file/context budget was curated for the target,
  not that this session proved a successful Colab load.
