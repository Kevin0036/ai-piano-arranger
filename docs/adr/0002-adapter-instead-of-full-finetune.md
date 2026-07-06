# ADR-0002: Foundation Model + Adapter Instead of Full Fine-Tuning

The Foundation Model (PiCoGen2) already encodes general piano arrangement capability — melody, harmony, rhythm, texture, and voice-leading. A user's Style or Preference represents a delta on top of that capability, not a replacement of it.

Full fine-tuning would:
1. Require retraining billions of parameters per Style (~10× GPU cost)
2. Risk catastrophic forgetting of general arrangement ability
3. Make each Style a full model copy (~several GB per Style)

Adapter-based training freezes the Foundation Model and trains only a small set of additional parameters per Style (~MB per Style). This makes it feasible to train on a personal GPU, store many Styles locally, and share Adapters without redistributing the full model.

Status: accepted

Considered Options:
- **Full fine-tuning** — higher quality potential per Style, but prohibitive cost and storage
- **Prompt/prefix tuning** — lighter than full tuning but requires recomputing prefix encoding per sample, less explored in music generation domain

Consequences:
- The Foundation Model version must be kept stable; an Adapter trained against v1 may not work with v2
- Adapter capacity limits how different the learned Style can be from the Foundation Model's default output
- The project can adopt newer PEFT methods as they emerge without changing the overall architecture
