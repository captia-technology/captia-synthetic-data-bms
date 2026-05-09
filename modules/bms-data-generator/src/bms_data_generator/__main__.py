"""Entry point: ``python -m bms_data_generator``."""

import uvicorn

from bms_data_generator.config import get_settings
from bms_data_generator.logging_config import setup_logging


def main() -> None:
    settings = get_settings()
    setup_logging(level=settings.log_level)
    uvicorn.run(
        "bms_data_generator.main:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
