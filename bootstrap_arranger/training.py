from __future__ import annotations

import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader
import yaml

from .bundles import BootstrapBundleDataset, load_bundle_records
from .decoder_io import build_picogen_decoder_batch
from .model import BootstrapConditionAdapter
from .paths import resolve_picogen_root


@dataclass
class BootstrapTrainingConfig:
    manifest_path: Path
    bundle_root: Path
    bundle_ids: list[str]
    feature_tag: str
    alignment_filename: str
    checkpoint_dir: Path
    seed: int
    device: str
    epochs: int
    batch_size: int
    learning_rate: float
    weight_decay: float
    alignment_weight: float
    global_weight: float
    variance_weight: float
    covariance_weight: float
    d_model: int
    hidden_dim: int
    dropout: float
    decoder_enabled: bool
    decoder_use_pretrained: bool
    picogen_root: Path
    picogen_config_file: Path | None
    picogen_checkpoint_file: Path | None
    max_seq_len: int
    bos_token_id: int


def _set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def _variance_loss(features: torch.Tensor, eps: float = 1e-4) -> torch.Tensor:
    std = torch.sqrt(features.var(dim=0, unbiased=False) + eps)
    return torch.relu(1.0 - std).mean()


def _covariance_loss(features: torch.Tensor) -> torch.Tensor:
    centered = features - features.mean(dim=0, keepdim=True)
    cov = centered.transpose(0, 1) @ centered / max(features.size(0) - 1, 1)
    off_diag = cov - torch.diag(torch.diag(cov))
    return off_diag.pow(2).mean()


def _gather_aligned_pairs(
    source_local: torch.Tensor,
    render_local: torch.Tensor,
    alignment_path: list[list[int]],
) -> tuple[torch.Tensor, torch.Tensor]:
    src_indices = torch.tensor([pair[0] for pair in alignment_path], dtype=torch.long, device=source_local.device)
    tgt_indices = torch.tensor([pair[1] for pair in alignment_path], dtype=torch.long, device=render_local.device)
    return source_local.index_select(0, src_indices), render_local.index_select(0, tgt_indices)


def _load_picogen_decoder(config: BootstrapTrainingConfig, device: str):
    picogen_root = resolve_picogen_root(config.picogen_root)
    if str(picogen_root) not in sys.path:
        sys.path.insert(0, str(picogen_root))
    from picogen2.model import PiCoGenDecoder
    from picogen2.utils import load_config

    if not config.decoder_use_pretrained:
        if config.picogen_config_file is None:
            raise ValueError("decoder.config_file is required when decoder.use_pretrained=false")
        hp = load_config(config.picogen_config_file)
        model = PiCoGenDecoder(hp).to(device)
        model.eval()
        return model

    checkpoint_file = None
    if config.picogen_checkpoint_file and config.picogen_checkpoint_file.exists():
        checkpoint_file = config.picogen_checkpoint_file
    return PiCoGenDecoder.from_pretrained(
        ckpt_file=checkpoint_file,
        config_file=config.picogen_config_file,
        device=device,
    )


def load_training_config(config_path: Path) -> BootstrapTrainingConfig:
    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    decoder = data.get("decoder", {})
    return BootstrapTrainingConfig(
        manifest_path=Path(data["dataset"]["manifest_path"]),
        bundle_root=Path(data["dataset"]["bundle_root"]),
        bundle_ids=list(data["dataset"]["bundle_ids"]),
        feature_tag=str(data["dataset"]["feature_tag"]),
        alignment_filename=str(data["dataset"].get("alignment_filename", "audio_to_render.bootstrap.json")),
        checkpoint_dir=Path(data["training"]["checkpoint_dir"]),
        seed=int(data["training"].get("seed", 1234)),
        device=str(data["training"].get("device", "cpu")),
        epochs=int(data["training"]["epochs"]),
        batch_size=int(data["training"].get("batch_size", 1)),
        learning_rate=float(data["training"]["learning_rate"]),
        weight_decay=float(data["training"].get("weight_decay", 0.0)),
        alignment_weight=float(data["training"].get("alignment_weight", 1.0)),
        global_weight=float(data["training"].get("global_weight", 0.25)),
        variance_weight=float(data["training"].get("variance_weight", 0.1)),
        covariance_weight=float(data["training"].get("covariance_weight", 0.01)),
        d_model=int(data["model"]["d_model"]),
        hidden_dim=int(data["model"]["hidden_dim"]),
        dropout=float(data["model"].get("dropout", 0.1)),
        decoder_enabled=bool(decoder.get("enabled", False)),
        decoder_use_pretrained=bool(decoder.get("use_pretrained", True)),
        picogen_root=Path(decoder.get("picogen_root", "third_party/picogen2")),
        picogen_config_file=Path(decoder["config_file"]) if decoder.get("config_file") else None,
        picogen_checkpoint_file=Path(decoder["checkpoint_file"]) if decoder.get("checkpoint_file") else None,
        max_seq_len=int(decoder.get("max_seq_len", 1024)),
        bos_token_id=int(decoder.get("bos_token_id", 1)),
    )


def train_overfit(config: BootstrapTrainingConfig) -> Path:
    _set_seed(config.seed)
    device = torch.device(config.device)

    records = load_bundle_records(config.manifest_path, config.bundle_root, config.bundle_ids)
    dataset = BootstrapBundleDataset(records, feature_tag=config.feature_tag, alignment_filename=config.alignment_filename)
    if len(dataset) == 0:
        raise ValueError("No bundles are ready for bootstrap training.")

    sample = dataset[0]
    input_dim = int(sample["source_features"].size(-1))
    model = BootstrapConditionAdapter(
        input_dim=input_dim,
        d_model=config.d_model,
        hidden_dim=config.hidden_dim,
        dropout=config.dropout,
    ).to(device)

    decoder = None
    if config.decoder_enabled:
        if config.picogen_config_file is None:
            raise ValueError("decoder.config_file is required when decoder.enabled=true")
        decoder = _load_picogen_decoder(config, str(device))
        for parameter in decoder.parameters():
            parameter.requires_grad_(False)

    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    loader = DataLoader(dataset, batch_size=config.batch_size, shuffle=True, collate_fn=lambda items: items)
    checkpoint_dir = config.checkpoint_dir
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    history: list[dict[str, float]] = []
    for epoch in range(config.epochs):
        total_loss = 0.0
        total_decoder_loss = 0.0
        model.train()
        for batch_items in loader:
            optimizer.zero_grad()
            batch_loss = torch.tensor(0.0, device=device)
            batch_decoder_loss = torch.tensor(0.0, device=device)

            for item in batch_items:
                source_features = item["source_features"].unsqueeze(0).to(device)
                render_features = item["render_features"].unsqueeze(0).to(device)
                alignment_path = item["alignment"]["path"]

                source_output = model.encode_source(source_features)
                render_output = model.encode_render(render_features)

                aligned_source, aligned_render = _gather_aligned_pairs(
                    source_output.local_conditions[0],
                    render_output.local_conditions[0],
                    alignment_path,
                )
                inv_loss = nn.functional.mse_loss(aligned_source, aligned_render)
                global_loss = nn.functional.mse_loss(
                    source_output.global_condition,
                    render_output.global_condition,
                )
                variance_loss = _variance_loss(aligned_source) + _variance_loss(aligned_render)
                covariance_loss = _covariance_loss(aligned_source) + _covariance_loss(aligned_render)

                loss = (
                    config.alignment_weight * inv_loss
                    + config.global_weight * global_loss
                    + config.variance_weight * variance_loss
                    + config.covariance_weight * covariance_loss
                )

                target_token_ids = item["target_token_ids"]
                if decoder is not None and target_token_ids is not None:
                    condition_embeddings = source_output.to_picogen_tensor()[0]
                    decoder_batch = build_picogen_decoder_batch(
                        condition_embeddings=condition_embeddings,
                        target_token_ids=target_token_ids.to(device),
                        max_seq_len=config.max_seq_len,
                        bos_token_id=config.bos_token_id,
                    )
                    decoder_out = decoder(
                        input_seqs=None,
                        input_ids=decoder_batch["input_ids"].to(device),
                        input_cond_embs=decoder_batch["input_cond_embs"].to(device),
                        input_cls_ids=decoder_batch["input_cls_ids"].to(device),
                        need_encode=decoder_batch["need_encode"].to(device),
                        labels=decoder_batch["label_ids"].to(device),
                    )
                    batch_decoder_loss = batch_decoder_loss + decoder_out["loss"]
                    loss = loss + decoder_out["loss"]

                batch_loss = batch_loss + loss

            batch_loss.backward()
            optimizer.step()
            total_loss += float(batch_loss.item())
            total_decoder_loss += float(batch_decoder_loss.item())

        history.append(
            {
                "epoch": float(epoch + 1),
                "loss": total_loss / max(len(loader), 1),
                "decoder_loss": total_decoder_loss / max(len(loader), 1),
            }
        )

    checkpoint_path = checkpoint_dir / "bootstrap_adapter.pt"
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "config": {
                "feature_tag": config.feature_tag,
                "bundle_ids": config.bundle_ids,
                "d_model": config.d_model,
                "hidden_dim": config.hidden_dim,
            },
            "history": history,
        },
        checkpoint_path,
    )
    (checkpoint_dir / "history.json").write_text(
        json.dumps(history, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return checkpoint_path
