import logging
import sys


def setup_logging(level_name: str = "INFO") -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)-35s │ %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))

    root = logging.getLogger()
    if root.handlers:
        root.handlers.clear()
    root.setLevel(level)
    root.addHandler(handler)

    # Silence noisy third-party loggers unless we're at DEBUG
    if level > logging.DEBUG:
        for noisy in ("httpx", "httpcore", "chromadb", "sqlalchemy.engine",
                      "uvicorn.access", "openai", "anthropic"):
            logging.getLogger(noisy).setLevel(logging.WARNING)
