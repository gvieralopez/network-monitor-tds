import logging
import os

import network_monitor_tds

logger = logging.getLogger(__name__)

COOKIE_PYRATE_VERSION = os.getenv("COOKIE_PYRATE_VERSION", "Not Set")


def main() -> None:
    pkg = "network_monitor_tds"
    version = network_monitor_tds.__version__

    logger.info("Package '%s' installed with version: %s", pkg, version)
    logger.info("Generated using Cookie Pyrate Version: %s", COOKIE_PYRATE_VERSION)

    logger.info("Life is beautiful!")


if __name__ == "__main__":
    main()
