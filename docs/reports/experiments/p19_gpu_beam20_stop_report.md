# P19 GPU Beam20 Stop Report

Date: 2026-06-29

## Summary

P19 real HF N-best extraction was retried on an available CUDA GPU and is stopped here.

Result:

- GPU was available: NVIDIA GeForce RTX 4080 SUPER, 16GB class.
- Dataset was available: `/data/MyProject/stt/data-gen/aig-audio-3/data/processed/hf_dataset`.
- Target split was `validation`: 424 rows, 420 rows selected after duration filtering.
- Model was `openai/whisper-large-v3`.
- Decode target stayed unchanged: `num_beams=20`, `num_return_sequences=20`.
- No N-best artifacts were written.
- Blocker is CUDA OOM, not missing GPU.

## What Was Tried

### Attempt 1: CUDA, default model dtype

The full validation extraction was run with HF local cache and CUDA.

Outcome:

- Failed with CUDA OOM before any artifact was written.
- The run confirmed that default model loading plus beam20/return20 is infeasible on the current GPU.

### Attempt 2: CUDA, auto fp16, explicit attention mask

The extractor was updated to reduce avoidable GPU memory use:

- Added `--torch-dtype`.
- `--torch-dtype auto` resolves to fp16 on CUDA and float32 on CPU.
- Processor now requests `return_attention_mask=True`.
- Generate receives the real attention mask when available.
- Unit tests cover dtype selection and generation input preparation.

Outcome:

- Failed again with CUDA OOM.
- This indicates the blocker is primarily `whisper-large-v3` beam20/return20 generation memory, not only fp32 model weights or missing attention mask.

## Current Blocker

Current evidence supports this blocker statement:

```text
HF Transformers `openai/whisper-large-v3` with num_beams=20 and
num_return_sequences=20 is infeasible on the available 16GB GPU for
the selected validation extraction. fp16 model loading and explicit
attention masks do not make this setting fit.
```

P19 should remain blocked unless one of these changes is explicitly accepted:

- Use a larger GPU.
- Use a smaller Whisper model.
- Reduce `num_beams` / `num_return_sequences`.
- Use another runtime that materially reduces generation memory.
- Split P19 into a memory-sweep phase before full N-best extraction.

## OpenFST / Kaldi Graph Review

The project design already contains the graph direction:

```text
Whisper N-best hypotheses + scores
-> weighted N-best acceptor A_x
-> correction WFST C
-> A_x o C
-> shortest path
```

However, the current implementation is not a real OpenFST graph backend.

Current state:

- P2 documents that Pynini/OpenFST is unavailable in the current uv/Python environment.
- P5 implements a deterministic phrase-rule fallback.
- The current correction engine is useful for contract and safety tests, but it is not Kaldi-style graph composition.

If the project should move closer to Kaldi-style graph decoding, a later phase needs to make Pynini/OpenFST a first-class backend:

- fixed runtime environment, likely Python/conda/docker constrained by Pynini availability;
- UTF-8 Korean acceptor/transducer smoke tests;
- weighted N-best acceptor construction;
- identity-safe correction transducer construction;
- real `compose -> shortestpath -> project output` tests;
- fallback-vs-OpenFST consistency tests.

## Scoring Review

The current Whisper WFST design is closer to N-best reranking than Kaldi decoding.

Current objective:

```text
final_cost(h, y) =
  ASR_cost(h | audio)
  + lambda * CorrectionCost(h -> y)
```

This is approximately:

```text
P_Whisper(h | audio) * P_Correction(y | h)
```

It is not the same as directly scoring:

```text
P_Whisper(y | audio)
```

Kaldi GMM-HMM decoding usually combines acoustic likelihoods from the acoustic model with path costs from the HCLG graph during search. HCLG contains HMM topology, context dependency, lexicon, and grammar/language-model structure. The acoustic score is not inside `G`; it is accumulated during decoding against graph paths.

Therefore the user's intuition is mostly right but needs this distinction:

- Kaldi: acoustic model score + graph path score are accumulated during decoding.
- Current project: Whisper already produces finished N-best text hypotheses, then correction cost reranks or rewrites them afterward.
- A corrected output may not have been directly scored by Whisper as a full output sequence.

If a domain LM is later added, the objective would become something like:

```text
Whisper_Nbest_cost
+ lambda_correction * CorrectionCost
+ lambda_lm * DomainLMCost
```

That would require separate calibration and safety gates. A strong domain LM or domain sentence acceptor can pull free conversation toward insurance-script text, which is why the current design prefers an identity-safe correction transducer first.

## Stop Decision

Stop P19 GPU extraction here.

Do not continue full extraction with the same `large-v3 + beam20 + return20` setting on this 16GB GPU.

