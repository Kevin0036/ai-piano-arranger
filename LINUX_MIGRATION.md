# Linux (Ubuntu 20.04, RTX 3090) 迁移指南

## 前置条件

- Ubuntu 20.04
- NVIDIA 驱动已安装（`nvidia-smi` 能正常输出）
- CUDA 已安装（`nvcc --version` 能正常输出）
- RTX 3090 (24GB VRAM)
- Git、Python 3.11、Conda 已安装

## 迁移步骤

### 1. 克隆代码

```bash
git clone https://github.com/Kevin0036/ai-piano-arranger.git
cd ai-piano-arranger
```

### 2. 创建 Conda 环境

```bash
conda create -n picogen2 python=3.11 -y
conda activate picogen2
```

### 3. 安装依赖

```bash
# 安装 PyTorch (CUDA 12.x，适配 3090)
conda install pytorch torchaudio pytorch-cuda=12.4 -c pytorch -c nvidia -y

# 安装项目核心依赖
cd PiCoGen
pip install -e .

# 安装额外依赖（beat_this、sheetsage 等）
pip install synctoolbox
pip install git+https://github.com/chenkigba/beat_this.git
pip install git+https://github.com/chenkigba/madmom.git

# 安装 Jukebox（用于高精度特征提取，需要 12GB+ VRAM）
pip install --no-build-isolation git+https://github.com/chenkigba/mirtoolkit_jukebox.git@mirtoolkit

# 安装 sheetsage（特征提取）
pip install --no-deps git+https://github.com/chenkigba/PiCoGen-sheetsage.git
pip install scipy pretty-midi validators pillow resampy librosa

cd ..
```

### 4. 下载模型权重

```bash
# PiCoGen2 模型权重（~77MB）
python -c "import picogen2.assets; picogen2.assets.checkpoint_file()"

# SheetSage 特征提取模型权重（~113MB）
python -c "from sheetsage.assets import retrieve_asset; retrieve_asset('SHEETSAGE_V02_HANDCRAFTED_MOMENTS')"
```

### 5. 验证安装

```bash
python -c "
import torch
print(f'CUDA: {torch.cuda.is_available()}, GPU: {torch.cuda.get_device_name(0)}, VRAM: {torch.cuda.get_device_properties(0).total_mem / 1024**3:.0f} GB')

from picogen2 import PiCoGenDecoder, Tokenizer
print('Picogen2 OK')

from beat_this.inference import Audio2Beats
print('beat_this OK')

import sheetsage
print('sheetsage OK')
"
```

### 6. 运行推理测试

```bash
# 准备好一个 MP3 测试文件，放在项目根目录
# 截取前 30 秒并转换
ffmpeg -y -i your_song.mp3 -t 30 -ar 22050 -ac 1 output/test_song.wav

# Jukebox 模型下载（如果需要高精度特征提取，~10.3GB）
# 下载后保存到 ~/.cache/jukebox/models/5b/prior_level_2.pth.tar

# 运行完整推理
python -c "
import warnings; warnings.filterwarnings('ignore')
import torch, time, picogen2
from picogen2 import PiCoGenDecoder, Tokenizer
from picogen2.mirtoolkit import beat_this, sheetsage

audio = 'output/test_song.wav'
print('Loading model...')
model = PiCoGenDecoder.from_pretrained(device='cuda')
tokenizer = Tokenizer()

print('Beat detection...')
beats, downbeats = beat_this.BeatThis(cuda=True, dbn=True)(audio)
beat_info = {'beats': beats.tolist(), 'downbeats': downbeats.tolist()}

print('Feature extraction (Jukebox)...')
ss = sheetsage.SheetSage()
out = ss(audio_path=audio, beat_information=beat_info, use_jukebox=True)

print('Generating piano...')
events = picogen2.decode(model=model, tokenizer=tokenizer,
    beat_information=beat_info,
    melody_last_embs=out['melody_last_hidden_state'],
    harmony_last_embs=out['harmony_last_hidden_state'],
    device='cuda')

midi = tokenizer.events_to_midi(events)
midi.dump('output/piano_output.mid')
print(f'Done. MIDI saved. Peak VRAM: {torch.cuda.max_memory_allocated() / 1024**2:.0f} MB')
"
```

## 已知差异（Windows → Linux）

| 项目 | Windows (当前) | Linux (目标) |
|------|---------------|-------------|
| Python | 3.11 (conda) | 3.11 (conda) |
| PyTorch | 2.6.0+cu124 | 2.6.0+cu124 |
| GPU | RTX 4060 8GB | RTX 3090 24GB |
| Jukebox | ❌ 显存不足 | ✅ 24GB 足够 |
| madmom (DBN beat) | ❌ 编译失败 | ✅ conda install -c conda-forge madmom |
| 开发工具 | VSCode Extension | Claude Code CLI 或 VSCode |

## 后续工作

迁移完成后，继续推进阶段二（构建个人数据集）和阶段三（训练第一个 Adapter）。

项目文档位于：
- `CONTEXT.md` — 领域术语表
- `docs/architecture.md` — 技术架构
- `docs/adr/` — 架构决策记录
- `docs/project-vision.md` — 原始项目愿景（参考）
