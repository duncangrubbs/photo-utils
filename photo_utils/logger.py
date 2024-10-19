import structlog


def get_logger():
    logger: structlog.stdlib.BoundLogger = structlog.get_logger()
    return logger
