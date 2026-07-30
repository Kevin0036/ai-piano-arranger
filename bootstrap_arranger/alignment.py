from __future__ import annotations

from typing import Any

import torch
import torch.nn.functional as F


def cosine_distance_matrix(source: torch.Tensor, target: torch.Tensor) -> torch.Tensor:
    if source.ndim != 2 or target.ndim != 2:
        raise ValueError("cosine_distance_matrix expects [T, D] tensors.")
    source = F.normalize(source.float(), dim=-1)
    target = F.normalize(target.float(), dim=-1)
    return 1.0 - source @ target.transpose(0, 1)


def dtw_alignment_path(cost_matrix: torch.Tensor) -> list[tuple[int, int]]:
    if cost_matrix.ndim != 2:
        raise ValueError("dtw_alignment_path expects a [T1, T2] cost matrix.")
    rows, cols = cost_matrix.shape
    dp = torch.full((rows, cols), float("inf"))
    parent = [[(-1, -1) for _ in range(cols)] for _ in range(rows)]

    dp[0, 0] = cost_matrix[0, 0]
    for row in range(rows):
        for col in range(cols):
            if row == 0 and col == 0:
                continue
            candidates = []
            if row > 0:
                candidates.append((dp[row - 1, col], row - 1, col))
            if col > 0:
                candidates.append((dp[row, col - 1], row, col - 1))
            if row > 0 and col > 0:
                candidates.append((dp[row - 1, col - 1], row - 1, col - 1))
            best_cost, prev_row, prev_col = min(candidates, key=lambda item: float(item[0]))
            dp[row, col] = cost_matrix[row, col] + best_cost
            parent[row][col] = (prev_row, prev_col)

    path: list[tuple[int, int]] = []
    row, col = rows - 1, cols - 1
    while row >= 0 and col >= 0:
        path.append((row, col))
        prev_row, prev_col = parent[row][col]
        if prev_row < 0 or prev_col < 0:
            break
        row, col = prev_row, prev_col
    path.reverse()
    return path


def align_pooled_features(source: torch.Tensor, target: torch.Tensor) -> dict[str, Any]:
    cost_matrix = cosine_distance_matrix(source, target)
    path = dtw_alignment_path(cost_matrix)
    avg_cost = sum(float(cost_matrix[row, col]) for row, col in path) / max(len(path), 1)
    return {
        "source_steps": int(source.size(0)),
        "target_steps": int(target.size(0)),
        "path": [[int(row), int(col)] for row, col in path],
        "mean_cost": avg_cost,
    }
