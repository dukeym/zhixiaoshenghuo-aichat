import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def safe_text(value):
    """移除 UTF-8 无法编码的 Unicode surrogate，保留正常字符。"""
    if not isinstance(value, str):
        return value
    return value.encode("utf-8", errors="replace").decode("utf-8")


class SafeTextFilter(logging.Filter):
    def filter(self, record):
        record.msg = safe_text(record.msg)
        if isinstance(record.args, tuple):
            record.args = tuple(safe_text(item) for item in record.args)
        elif isinstance(record.args, dict):
            record.args = {key: safe_text(value) for key, value in record.args.items()}
        return True


def get_logger(name: str) -> logging.Logger:
    """创建同时输出到终端和滚动文件的日志器。"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = RotatingFileHandler(
        Path(f"{name}.log"),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    console_handler = logging.StreamHandler()
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    file_handler.addFilter(SafeTextFilter())
    console_handler.addFilter(SafeTextFilter())
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.propagate = False
    return logger
