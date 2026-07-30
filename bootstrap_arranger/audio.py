from __future__ import annotations

import math
import subprocess
from dataclasses import dataclass
from pathlib import Path

import torch
import torch.nn.functional as F
import torchaudio


@dataclass
class AudioFeatureExtractorConfig:
    backend: str
    model_name_or_path: str
    sample_rate: int = 24000
    pool_seconds: float = 0.5
    max_steps: int = 512
    inference_chunk_seconds: float = 20.0
    local_files_only: bool = False
    trust_remote_code: bool = False
    device: str = "cpu"


@dataclass
class AudioFeatureCache:
    pooled_features: torch.Tensor
    hidden_states: torch.Tensor
    duration_sec: float
    frame_rate: float
    backend: str
    model_name_or_path: str

    def to_serializable(self) -> dict[str, object]:
        return {
            "pooled_features": self.pooled_features.cpu(),
            "hidden_states": self.hidden_states.cpu(),
            "duration_sec": float(self.duration_sec),
            "frame_rate": float(self.frame_rate),
            "backend": self.backend,
            "model_name_or_path": self.model_name_or_path,
        }

    @classmethod
    def from_file(cls, path: Path) -> "AudioFeatureCache":
        payload = torch.load(path, map_location="cpu", weights_only=False)
        return cls(
            pooled_features=payload["pooled_features"].float(),
            hidden_states=payload["hidden_states"].float(),
            duration_sec=float(payload["duration_sec"]),
            frame_rate=float(payload["frame_rate"]),
            backend=str(payload["backend"]),
            model_name_or_path=str(payload["model_name_or_path"]),
        )


def load_audio_mono(audio_path: Path, sample_rate: int) -> tuple[torch.Tensor, int]:
    try:
        waveform, original_sample_rate = torchaudio.load(str(audio_path))
        if waveform.dim() == 2 and waveform.size(0) > 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        if waveform.dim() == 2:
            waveform = waveform.squeeze(0)
        if original_sample_rate != sample_rate:
            waveform = torchaudio.functional.resample(waveform, original_sample_rate, sample_rate)
        return waveform.contiguous(), sample_rate
    except (ImportError, OSError, RuntimeError):
        return _load_audio_with_ffmpeg(audio_path, sample_rate)


def _load_audio_with_ffmpeg(audio_path: Path, sample_rate: int) -> tuple[torch.Tensor, int]:
    command = [
        "ffmpeg",
        "-nostdin",
        "-v",
        "error",
        "-i",
        str(audio_path),
        "-f",
        "f32le",
        "-acodec",
        "pcm_f32le",
        "-ac",
        "1",
        "-ar",
        str(sample_rate),
        "-",
    ]
    result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if not result.stdout:
        raise ValueError(f"ffmpeg returned empty audio for {audio_path}")
    waveform = torch.frombuffer(bytearray(result.stdout), dtype=torch.float32).clone()
    return waveform.contiguous(), sample_rate


def pool_hidden_states(
    hidden_states: torch.Tensor,
    duration_sec: float,
    pool_seconds: float,
    max_steps: int,
) -> tuple[torch.Tensor, float]:
    if hidden_states.ndim != 2:
        raise ValueError(f"Expected [T, D] hidden states, got {tuple(hidden_states.shape)}")
    total_frames = hidden_states.size(0)
    if total_frames == 0:
        raise ValueError("Cannot pool empty hidden states.")

    frame_rate = total_frames / max(duration_sec, 1e-6)
    num_steps = max(1, math.ceil(duration_sec / max(pool_seconds, 1e-3)))
    num_steps = min(num_steps, max_steps)

    boundaries = torch.linspace(0, total_frames, steps=num_steps + 1).round().long()
    pooled = []
    for start, end in zip(boundaries[:-1], boundaries[1:]):
        start_idx = int(start.item())
        end_idx = int(end.item())
        if end_idx <= start_idx:
            pooled.append(hidden_states[min(start_idx, total_frames - 1)])
        else:
            pooled.append(hidden_states[start_idx:end_idx].mean(dim=0))
    return torch.stack(pooled, dim=0), frame_rate


class AudioFeatureExtractor:
    def __init__(self, config: AudioFeatureExtractorConfig):
        self.config = config

    def encode(self, waveform: torch.Tensor, sample_rate: int) -> AudioFeatureCache:
        if sample_rate != self.config.sample_rate:
            raise ValueError(
                f"Expected sample_rate={self.config.sample_rate}, got {sample_rate}. "
                "Use load_audio_mono() to normalize inputs."
            )

        hidden_states = self._encode_hidden_states(waveform, sample_rate).detach().cpu().float()
        duration_sec = waveform.numel() / sample_rate
        pooled_features, frame_rate = pool_hidden_states(
            hidden_states,
            duration_sec=duration_sec,
            pool_seconds=self.config.pool_seconds,
            max_steps=self.config.max_steps,
        )
        return AudioFeatureCache(
            pooled_features=pooled_features,
            hidden_states=hidden_states,
            duration_sec=duration_sec,
            frame_rate=frame_rate,
            backend=self.config.backend,
            model_name_or_path=self.config.model_name_or_path,
        )

    def encode_file(self, audio_path: Path) -> AudioFeatureCache:
        waveform, sample_rate = load_audio_mono(audio_path, self.config.sample_rate)
        return self.encode(waveform, sample_rate)

    def _encode_hidden_states(self, waveform: torch.Tensor, sample_rate: int) -> torch.Tensor:
        raise NotImplementedError


class MockAudioFeatureExtractor(AudioFeatureExtractor):
    def _encode_hidden_states(self, waveform: torch.Tensor, sample_rate: int) -> torch.Tensor:
        frame_samples = max(1, int(sample_rate * 0.02))
        num_frames = max(1, math.ceil(waveform.numel() / frame_samples))
        padded = F.pad(waveform, (0, num_frames * frame_samples - waveform.numel()))
        frames = padded.view(num_frames, frame_samples)
        means = frames.mean(dim=1)
        stds = frames.std(dim=1, unbiased=False)
        maxs = frames.max(dim=1).values
        mins = frames.min(dim=1).values
        energy = (frames**2).mean(dim=1)
        stats = torch.stack([means, stds, maxs, mins, energy], dim=1)
        repeats = math.ceil(64 / stats.size(1))
        expanded = stats.repeat(1, repeats)[:, :64]
        phase = torch.linspace(0.0, 1.0, steps=64, dtype=expanded.dtype)
        return expanded + phase.unsqueeze(0) * 0.01


class HuggingFaceMertFeatureExtractor(AudioFeatureExtractor):
    def __init__(self, config: AudioFeatureExtractorConfig):
        super().__init__(config)
        from transformers import AutoFeatureExtractor, AutoModel

        self.processor = AutoFeatureExtractor.from_pretrained(
            config.model_name_or_path,
            local_files_only=config.local_files_only,
            trust_remote_code=config.trust_remote_code,
        )
        self.model = AutoModel.from_pretrained(
            config.model_name_or_path,
            local_files_only=config.local_files_only,
            trust_remote_code=config.trust_remote_code,
        ).to(config.device)
        self.model.eval()
        for parameter in self.model.parameters():
            parameter.requires_grad_(False)

    def _encode_hidden_states(self, waveform: torch.Tensor, sample_rate: int) -> torch.Tensor:
        chunk_samples = max(1, int(self.config.inference_chunk_seconds * sample_rate))
        hidden_states: list[torch.Tensor] = []
        for start in range(0, waveform.numel(), chunk_samples):
            chunk = waveform[start : start + chunk_samples]
            inputs = self.processor(
                chunk.cpu().numpy(),
                sampling_rate=sample_rate,
                return_tensors="pt",
            )
            inputs = {key: value.to(self.config.device) for key, value in inputs.items()}
            with torch.inference_mode():
                outputs = self.model(**inputs)
            hidden_states.append(outputs.last_hidden_state[0].detach().cpu())
            if self.config.device.startswith("cuda"):
                torch.cuda.empty_cache()
        return torch.cat(hidden_states, dim=0)


def create_audio_feature_extractor(config: AudioFeatureExtractorConfig) -> AudioFeatureExtractor:
    backend = config.backend.lower()
    if backend == "mock":
        return MockAudioFeatureExtractor(config)
    if backend in {"hf_mert", "mert", "huggingface_mert"}:
        return HuggingFaceMertFeatureExtractor(config)
    raise ValueError(f"Unsupported audio encoder backend: {config.backend}")
