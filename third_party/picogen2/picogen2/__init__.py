from .version import VERSION, VERSION_SHORT

__all__ = ["decode", "PiCoGenDecoder", "Tokenizer", "VERSION", "VERSION_SHORT"]


def __getattr__(name):
    if name == "Tokenizer":
        from .repr import Tokenizer

        return Tokenizer
    if name == "PiCoGenDecoder":
        from .model import PiCoGenDecoder

        return PiCoGenDecoder
    if name == "decode":
        from .infer import decode

        return decode
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
