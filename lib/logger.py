import structlog


def get_logger():
    logger = structlog.get_logger()
    return logger
