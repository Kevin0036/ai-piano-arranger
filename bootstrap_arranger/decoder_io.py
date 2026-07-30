from __future__ import annotations

import torch


def build_picogen_decoder_batch(
    condition_embeddings: torch.Tensor,
    target_token_ids: torch.Tensor,
    *,
    max_seq_len: int,
    bos_token_id: int,
) -> dict[str, torch.Tensor]:
    if condition_embeddings.ndim != 3:
        raise ValueError("condition_embeddings must have shape [T, N, D].")
    if target_token_ids.ndim != 1:
        raise ValueError("target_token_ids must have shape [L].")

    total_tokens = 1 + condition_embeddings.size(0) + target_token_ids.numel()
    if total_tokens < 2:
        raise ValueError("Need at least one target token.")

    input_ids = torch.zeros(max_seq_len, dtype=torch.long)
    input_cond_embs = torch.zeros(
        max_seq_len,
        condition_embeddings.size(1),
        condition_embeddings.size(2),
        dtype=torch.float32,
    )
    input_cls_ids = torch.zeros(max_seq_len, dtype=torch.long)
    need_encode = torch.zeros(max_seq_len, dtype=torch.bool)
    labels = torch.full((max_seq_len,), -100, dtype=torch.long)

    sequence_limit = min(total_tokens - 1, max_seq_len)
    input_ids[0] = bos_token_id

    cursor = 1
    for cond_idx in range(condition_embeddings.size(0)):
        if cursor >= sequence_limit:
            break
        input_cond_embs[cursor] = condition_embeddings[cond_idx]
        input_cls_ids[cursor] = 1
        need_encode[cursor] = True
        cursor += 1

    labels_cursor = cursor - 1
    for token_idx in range(target_token_ids.numel()):
        if cursor >= sequence_limit:
            break
        input_ids[cursor] = target_token_ids[token_idx]
        input_cls_ids[cursor] = 0
        cursor += 1
        if labels_cursor < max_seq_len:
            labels[labels_cursor] = target_token_ids[token_idx]
            labels_cursor += 1

    return {
        "input_ids": input_ids.unsqueeze(0),
        "input_cond_embs": input_cond_embs.unsqueeze(0),
        "input_cls_ids": input_cls_ids.unsqueeze(0),
        "need_encode": need_encode.unsqueeze(0),
        "label_ids": labels.unsqueeze(0),
    }
