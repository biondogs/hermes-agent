> Status: superseded by hermes-estate/docs/OPERATIONS.md §8 — probe receipt (2026-10-26, ER2-F t_b74a695d). Kept unchanged below as historical record.

# QWEN36-FAST-TRUE-CTX — probe report (2026-10-23, card t_7cb89ed9)

**Verdict: the effective context window of the `qwen36-fast` orb alias is 131,072 tokens. The operator's 262,144 suspicion is true of the underlying model weights but NOT of the served deployment. The current Hermes pin (`context_length: 131072`) is correct and must NOT change. No config was modified.**

## 1. Upstream identification (read-only discovery)

- orb alias `qwen36-fast` → LiteLLM DB model `model: qwen36-35b`, `custom_llm_provider: openai`, credential `gh201` (from `GET /model/info` on orb, HTTP 200 with the fleet virtual key).
- Served on **gh201** as vLLM (`ps` read, read-only ssh):
  ```
  vllm serve Qwen/Qwen3.6-35B-A3B-FP8 --served-model-name qwen36-35b \
    --max-model-len 131072 --gpu-memory-utilization 0.55 --max-num-seqs 16 \
    --enable-prefix-caching --enable-chunked-prefill ... --port 8000
  ```
  → **deployment cap `--max-model-len 131072`**. This is the number that binds.
- Native model window (HF `Qwen/Qwen3.6-35B-A3B-FP8` config.json, text_config): **`max_position_embeddings: 262144`** (qwen3_5_moe MoE, rope_theta 1e7, partial_rope 0.25). The 262K headroom exists in the weights but is unused by this deployment.
- LiteLLM DB `model_info` for the alias: `max_input_tokens: 131072`, `max_output_tokens: 131072` — consistent with the deployment, no understatement at the orb layer either.

## 2. Empirical position probe (needle-in-haystack via orb /v1/chat/completions)

Filler = numbered logistics sentences; needle = unique `ZULU-<6 digits>-NEST` access code inserted at 85% depth; temperature 0; exact `usage.prompt_tokens` recorded from the server (upstream tokenizer = ground truth).

| probe | prompt_chars | prompt_tokens | result |
|---|---|---|---|
| calibration | 18,408 | 3,735 | OK (truncated output, max_tokens=24, rewritten in v2) |
| target 120K | 609,504 | 127,019 | accepted (needle located mid-reasoning) |
| target 128K | 650,272 | ≥131,073 (est) | **HTTP 400 ContextWindowExceededError** |
| target 133K / 145K / 190K / 262K / 268K | 675K–1,362K | ≫131K | **HTTP 400, identical error** |
| v2 retrieval 5K | 24,650 | 5,012 | needle retrieved, finish=stop |
| v2 near-cap PASS | 628,112 | **130,928** | **needle retrieved verbatim** ("The code is ZULU-561580-NEST"), finish=length at exactly **144 completion tokens** → 130,928 + 144 = **131,072 exactly** (vLLM total-budget arithmetic proof) |
| v2 near-cap FAIL | 645,136–647,376 | est ~134–135K | HTTP 400, same error |

Rejection error (identical for every oversized prompt, relayed through LiteLLM):

```
HTTP 400 {"error":{"message":"litellm.ContextWindowExceededError: litellm.BadRequestError:
ContextWindowExceededError: OpenAIException - This model's maximum context length is
131072 tokens. However, your prompt contains at least 131073 input tokens, which exceeds
this limit even without any output tokens. (parameter=input_tokens, value=131073)"}}
```

The `OpenAIException` wrapper = the error originated at the upstream OpenAI-compatible server (vLLM) and was relayed by LiteLLM, not generated at the proxy.

## 3. Which limit binds

- **Binding: the vLLM deployment `--max-model-len 131072` on gh201** (physical limit).
- LiteLLM DB `max_input_tokens: 131072` coincides with it, so orb metadata is not understating either.
- Native model 262,144 is NOT reachable through this deployment.
- To ever serve 262K, BOTH would be required (operator decision; NOT done, out of this card's scope): redeploy gh201 vLLM with `--max-model-len 262144` (may need higher `--gpu-memory-utilization` or KV-cache headroom review) AND raise the LiteLLM DB `max_input_tokens` for the alias. Until then, all pins stay 131072.

Probe cliff precision: largest accepted prompt = 130,928 tokens; all prompts ≥ ~131,073 rejected; accepted-prompt leftover output budget = exactly (131,072 − prompt_tokens). The cliff is 131,072 to the token.

## 4. Fleet pin state (premise correction + verification sweep)

- **Root config** `~/.hermes/config.yaml`: `providers.litellm.models.qwen36-fast: context_length: 131072, max_tokens: 32768` — **correct, unchanged**.
- **Correction to the card's premise**: NO profile config carries a `qwen36-fast:` models pin. All 59 profiles reference `qwen36-fast` only inside `auxiliary:` blocks (compression, approval, mcp, title_generation, memory_query_rewrite, profile_describer, review, skills_hub, web_extract). `grep "qwen36-fast:" ~/.hermes/profiles/*/config.yaml` → zero matches. They resolve context from gateway metadata, which orb reports as `max_input_tokens: 131072` on `/v1/models` — also correct, so no understate is possible through that path either.
- Both pins (131,072 / 32,768) verified live against the measured end-to-end behavior; no before/after diff exists because **no change was warranted**: the operator pre-authorization was conditional on the probe PROVING 262K served, and it proved the opposite.

## 5. Comparison with the qwen38-flash-fp8 precedent

qwen38-flash-fp8 was a genuine understate (pin 131K < real 262K served by gh207:8001; LiteLLM DB now shows `max_input_tokens: 262144` for it, and fleet pins were corrected to 262144). qwen36-fast is the mirror case: metadata pinned 131K and the deployment genuinely serves 131K — the 262K figure was the model's native window, not the served window. Precedent resolved: no bug here.

## 6. Receipts

- Probe scripts + raw JSONL transcripts: `probes/needle_probe.py`, `probes/needle_probe_v2.py`, `probes/final_nearcap.py`, `probes/probe_transcript.jsonl`, `probes/probe_transcript_v2.jsonl` (workspace t_7cb89ed9; copies attached to card t_7cb89ed9).
- Upstream evidence: `ps` output from gh201 (vLLM serve line, 2026-10-23), HF config.json `max_position_embeddings`, orb `/model/info` and `/v1/models` responses.
- All discovery read-only; aistack laws respected (no litellm/orb mutations, no restarts, fleet vLLM process untouched).
