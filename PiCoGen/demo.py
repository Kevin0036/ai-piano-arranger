#!/usr/bin/env python3
"""
PiCoGen2 Demo - 将流行音乐转换为钢琴演奏版本

使用方法:
    python demo.py                          # 使用默认配置
    python demo.py --audio your_song.mp3    # 指定音频文件
    python demo.py --output output.mid      # 指定输出路径

依赖:
    pip install picogen2
    # 或从源码安装: pip install -e .
"""

import warnings
warnings.filterwarnings('ignore')

import argparse
import json
import tempfile
from pathlib import Path

import numpy as np
import torch

from picogen2 import PiCoGenDecoder, Tokenizer, decode
from picogen2.infer import detect_beat, extract_sheetsage_feature


def main():
    parser = argparse.ArgumentParser(
        description="PiCoGen2 Demo - 流行音乐转钢琴演奏",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python demo.py --audio "张信哲 - 爱如潮水.mp3"
    python demo.py --audio song.wav --output piano.mid --temperature 0.8
        """
    )
    parser.add_argument(
        "--audio", "-a",
        type=str,
        default=r"C:\Users\chen\Desktop\张信哲 - 爱如潮水.mp3",
        help="输入音频文件路径 (支持 mp3, wav, flac 等格式)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default=None,
        help="输出 MIDI 文件路径 (默认: <audio_name>_piano.mid)"
    )
    parser.add_argument(
        "--temperature", "-t",
        type=float,
        default=1.0,
        help="生成温度 (0.0-2.0, 越高越随机, 默认: 1.0)"
    )
    parser.add_argument(
        "--max-bars",
        type=int,
        default=None,
        help="最大生成小节数 (默认: 处理整首歌)"
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="计算设备 (cuda/cpu, 默认: 自动检测)"
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="保留中间临时文件 (用于调试)"
    )
    parser.add_argument(
        "--no-jukebox",
        action="store_true",
        help="禁用 Jukebox 特征提取 (使用手工特征, 更快但可能影响质量)"
    )

    args = parser.parse_args()

    # 验证输入文件
    audio_path = Path(args.audio)
    if not audio_path.exists():
        print(f"[错误] 音频文件不存在: {audio_path}")
        return 1

    # 设置输出路径
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = audio_path.parent / f"{audio_path.stem}_piano.mid"

    # 检测设备
    if args.device:
        device = args.device
    else:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    print("=" * 50)
    print("PiCoGen2 - 流行音乐转钢琴演奏")
    print("=" * 50)
    print(f"输入音频: {audio_path}")
    print(f"输出 MIDI: {output_path}")
    print(f"计算设备: {device}")
    if device == "cuda":
        print(f"GPU: {torch.cuda.get_device_name(0)}")
    print(f"生成温度: {args.temperature}")
    if args.max_bars:
        print(f"最大小节: {args.max_bars}")
    print("=" * 50)

    # 创建临时目录
    if args.keep_temp:
        temp_dir = Path("./picogen_temp")
        temp_dir.mkdir(exist_ok=True)
        cleanup = lambda: None
    else:
        # Windows: 使用 ignore_cleanup_errors=True 避免文件锁定问题
        temp_context = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        temp_dir = Path(temp_context.name)
        cleanup = temp_context.cleanup

    try:
        beat_file = temp_dir / "beats.json"
        sheetsage_file = temp_dir / "sheetsage.npz"

        # Step 1: 检测节拍
        print("\n[1/4] 检测节拍...")
        detect_beat(audio_path, beat_file)

        with open(beat_file, 'r') as f:
            beat_information = json.load(f)

        num_beats = len(beat_information["beats"])
        num_downbeats = len(beat_information["downbeats"])
        print(f"      检测到 {num_beats} 个节拍, {num_downbeats} 个下拍")

        # Step 2: 提取音频特征
        use_jukebox = not args.no_jukebox
        print(f"\n[2/4] 提取音频特征 (SheetSage, jukebox={use_jukebox})...")
        extract_sheetsage_feature(audio_path, sheetsage_file, beat_file, use_jukebox=use_jukebox)

        sheetsage_data = np.load(sheetsage_file)
        melody_embs = sheetsage_data["melody"]
        harmony_embs = sheetsage_data["harmony"]
        print(f"      旋律特征: {melody_embs.shape}")
        print(f"      和声特征: {harmony_embs.shape}")

        # Step 3: 加载模型
        print("\n[3/4] 加载模型...")
        model = PiCoGenDecoder.from_pretrained(device=device)
        tokenizer = Tokenizer()
        print(f"      模型参数量: {sum(p.numel() for p in model.parameters()):,}")

        # Step 4: 生成 MIDI
        print("\n[4/4] 生成钢琴演奏...")
        output_events = decode(
            model=model,
            tokenizer=tokenizer,
            beat_information=beat_information,
            melody_last_embs=melody_embs,
            harmony_last_embs=harmony_embs,
            max_bar_num=args.max_bars,
            temperature=args.temperature,
            device=device,
        )

        # 保存 MIDI
        midi = tokenizer.events_to_midi(output_events)
        midi.dump(str(output_path))

        # 统计信息
        num_notes = sum(len(inst.notes) for inst in midi.instruments) if midi.instruments else 0
        duration = midi.get_end_time() if hasattr(midi, 'get_end_time') else 0

        print("\n" + "=" * 50)
        print("生成完成!")
        print("=" * 50)
        print(f"输出文件: {output_path}")
        print(f"生成音符数: {num_notes}")
        print(f"时长: {duration:.2f} 秒")
        print("=" * 50)

        return 0

    except Exception as e:
        error_msg = str(e)
        print(f"\n[错误] 生成失败: {error_msg}")

        # 检查是否是 SheetSage 资源下载问题
        if "403" in error_msg and "Download failed" in error_msg:
            print("\n" + "=" * 60)
            print("【已知问题】SheetSage 模型资源无法自动下载")
            print("=" * 60)
            print("SheetSage 的 S3 存储桶已限制公共访问，这是上游问题。")
            print("参见: https://github.com/chrisdonahue/sheetsage/issues/44")
            print("\n【解决方案】手动下载模型文件:")
            print("1. 从 Mega.nz 下载备份文件:")
            print("   https://mega.nz/file/j9YyWbAK#LjROFI9qxGq6Om9dx9HaORd5NaiYOcV8ULVUBKB0bcg")
            print("2. 解压到 SheetSage 缓存目录:")
            if Path.home().drive:  # Windows
                print(f"   {Path.home() / '.sheetsage'}")
            else:
                print("   ~/.sheetsage/")
            print("3. 重新运行此脚本")
            print("=" * 60)
        else:
            import traceback
            traceback.print_exc()
        return 1
    finally:
        cleanup()


if __name__ == "__main__":
    exit(main())
