import shutil
import subprocess
import tempfile
from pathlib import Path

import torch
import torchaudio


def download(url, file):
    """Download a file from URL using Python's urllib (cross-platform).

    Tries direct connection first, then falls back to system proxy if direct fails.
    """
    import urllib.request
    import ssl

    assert isinstance(url, str)
    assert isinstance(file, (str, Path))
    if isinstance(file, str):
        file = Path(file)

    file.parent.mkdir(parents=True, exist_ok=True)

    # Create SSL context that doesn't verify certificates (for compatibility)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Try 1: Direct connection (no proxy)
    try:
        no_proxy_handler = urllib.request.ProxyHandler({})
        https_handler = urllib.request.HTTPSHandler(context=ssl_context)
        opener = urllib.request.build_opener(no_proxy_handler, https_handler)
        urllib.request.install_opener(opener)

        tmp_dir = tempfile.TemporaryDirectory()
        tmp_file = Path(tmp_dir.name) / file.name

        urllib.request.urlretrieve(url, str(tmp_file))
        shutil.move(str(tmp_file), str(file))
        return
    except Exception:
        pass  # Try with proxy

    # Try 2: Use system proxy
    try:
        urllib.request.install_opener(urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=ssl_context)
        ))

        tmp_dir = tempfile.TemporaryDirectory()
        tmp_file = Path(tmp_dir.name) / file.name

        urllib.request.urlretrieve(url, str(tmp_file))
        shutil.move(str(tmp_file), str(file))
    except Exception as e:
        print(f"Download failed: {e}")
        raise


def load_audio(
    path, dtype="float32", return_tensor=False, channels_first=False, mono=False, sr=None
):
    """
    Load an audio file from the given path.
    Args:
        path (str): The path to the audio file.
        dtype (str, optional): The desired data type of the audio waveform. Defaults to "float64".
        return_tensor (bool, optional): Whether to return the audio waveform as a tensor. Defaults to False.
        channels_first (bool, optional): Whether to return the audio waveform with channels as the first dimension. Defaults to False.
    Returns:
        tuple or ndarray: If `return_tensor` is False, returns a tuple containing the audio waveform as a numpy ndarray and the sample rate as an integer. If `return_tensor` is True, returns a tuple containing the audio waveform as a PyTorch tensor and the sample rate as an integer.
    """
    assert dtype in ["float32", "float64"]

    try:
        waveform, sample_rate = torchaudio.load(path, channels_first=channels_first)
        if mono and waveform.shape[0] > 1:
            if channels_first:
                waveform = waveform.mean(0)
            else:
                waveform = waveform.mean(-1)

        if dtype == "float64":
            waveform = waveform.to(dtype=torch.float64)

    except Exception:
        # in case torchaudio fails, try soundfile
        import soundfile as sf

        waveform, sample_rate = sf.read(path, dtype=dtype)
        waveform = torch.from_numpy(waveform)

    if sr is not None:
        # resample the audio to the given sample rate
        waveform = torchaudio.transforms.Resample(sample_rate, sr)(waveform)
        sample_rate = sr

    if not return_tensor:
        waveform = waveform.squeeze().numpy()

    return waveform, sample_rate
