from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import nn


class ViewProjector(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int, output_dim: int, dropout: float):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.net(features)


@dataclass
class BootstrapConditionOutput:
    local_conditions: torch.Tensor
    global_condition: torch.Tensor

    def to_picogen_tensor(self) -> torch.Tensor:
        time_steps = self.local_conditions.size(1)
        global_steps = self.global_condition.unsqueeze(1).expand(-1, time_steps, -1)
        return torch.stack([self.local_conditions, global_steps], dim=2)


class BootstrapConditionAdapter(nn.Module):
    def __init__(
        self,
        input_dim: int,
        d_model: int = 512,
        hidden_dim: int = 1024,
        dropout: float = 0.1,
    ):
        super().__init__()
        self.source_local = ViewProjector(input_dim, hidden_dim, d_model, dropout)
        self.render_local = ViewProjector(input_dim, hidden_dim, d_model, dropout)
        self.source_global = ViewProjector(input_dim, hidden_dim, d_model, dropout)
        self.render_global = ViewProjector(input_dim, hidden_dim, d_model, dropout)

    def encode_source(self, source_features: torch.Tensor) -> BootstrapConditionOutput:
        local = self.source_local(source_features)
        pooled = source_features.mean(dim=1)
        global_condition = self.source_global(pooled)
        return BootstrapConditionOutput(local_conditions=local, global_condition=global_condition)

    def encode_render(self, render_features: torch.Tensor) -> BootstrapConditionOutput:
        local = self.render_local(render_features)
        pooled = render_features.mean(dim=1)
        global_condition = self.render_global(pooled)
        return BootstrapConditionOutput(local_conditions=local, global_condition=global_condition)
