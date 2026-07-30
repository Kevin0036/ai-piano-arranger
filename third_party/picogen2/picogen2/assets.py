import shutil
import subprocess
from pathlib import Path

from .utils import logger

CACHE_DIR = Path.home() / ".cache" / "picogen2"

URL_MODEL = "https://zenodo.org/records/13380452/files/model_ft_00070000?download=1"
URL_VOCAB = "https://raw.githubusercontent.com/tanchihpin0517/PiCoGen/v2/assets/vocab.json"
URL_CONFIG = "https://raw.githubusercontent.com/tanchihpin0517/PiCoGen/v2/assets/config.json"
URL_TEST_SONG = "https://www.dropbox.com/scl/fi/zj68yghtn0cwtwnqj7vrx/pop.00000.wav?rlkey=bejuh89wehbc8psl9ujmqa73u&st=kb265uvz&dl=0"


def default_cache_dir_decorator(func):
    def wrapper(*args, **kwargs):
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        return func(*args, **kwargs)

    return wrapper


@default_cache_dir_decorator
def checkpoint_file():
    default_ckpt_file = CACHE_DIR / "model_ft_00070000"
    if not default_ckpt_file.exists():
        logger.warning("Download default model from {}".format(URL_MODEL))
        logger.warning("Save to {}".format(default_ckpt_file))

        _download(URL_MODEL, default_ckpt_file)

    return default_ckpt_file


@default_cache_dir_decorator
def vocab_file():
    default_vocab_file = CACHE_DIR / "vocab.json"
    if not default_vocab_file.exists():
        logger.warning("Download default vocab from {}".format(URL_VOCAB))
        logger.warning("Save to {}".format(default_vocab_file))

        _download(URL_VOCAB, default_vocab_file)

    return default_vocab_file


@default_cache_dir_decorator
def config_file():
    default_config_file = CACHE_DIR / "config.json"
    if not default_config_file.exists():
        logger.warning("Download default config from {}".format(URL_CONFIG))
        logger.warning("Save to {}".format(default_config_file))

        _download(URL_CONFIG, default_config_file)

    return default_config_file


@default_cache_dir_decorator
def test_song():
    default_test_song = CACHE_DIR / "pop.00000.wav"
    if not default_test_song.exists():
        logger.warning("Download default test song from {}".format(URL_TEST_SONG))
        logger.warning("Save to {}".format(default_test_song))

        _download(URL_TEST_SONG, default_test_song)

    return default_test_song


def _download(url, output_file_path, verbose=True):
    """Download a file from URL using Python's urllib (cross-platform).

    Tries direct connection first, then falls back to system proxy if direct fails.
    """
    import urllib.request
    import ssl
    import os

    if verbose:
        logger.info(f"Downloading {url} to {output_file_path}")

    output_file_path = Path(output_file_path)
    output_file_path.parent.mkdir(parents=True, exist_ok=True)

    # Download with progress indication
    def _report_progress(block_num, block_size, total_size):
        if total_size > 0:
            percent = min(100, block_num * block_size * 100 // total_size)
            if block_num % 100 == 0:  # Print every 100 blocks
                logger.info(f"Download progress: {percent}%")

    # Create SSL context that doesn't verify certificates (for compatibility)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Try 1: Direct connection (no proxy)
    try:
        logger.info("Trying direct connection...")
        no_proxy_handler = urllib.request.ProxyHandler({})
        https_handler = urllib.request.HTTPSHandler(context=ssl_context)
        opener = urllib.request.build_opener(no_proxy_handler, https_handler)
        urllib.request.install_opener(opener)

        urllib.request.urlretrieve(url, str(output_file_path), reporthook=_report_progress)

        if verbose:
            logger.info(f"Download complete: {output_file_path}")
        return
    except Exception as e1:
        logger.warning(f"Direct connection failed: {e1}")
        if output_file_path.exists():
            output_file_path.unlink()

    # Try 2: Use system proxy
    try:
        logger.info("Trying with system proxy...")
        # Reset to default opener (uses system proxy)
        urllib.request.install_opener(urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=ssl_context)
        ))

        urllib.request.urlretrieve(url, str(output_file_path), reporthook=_report_progress)

        if verbose:
            logger.info(f"Download complete: {output_file_path}")
        return
    except Exception as e2:
        logger.error(f"Failed to download file from {url}: {e2}")
        if output_file_path.exists():
            output_file_path.unlink()
        raise e2
