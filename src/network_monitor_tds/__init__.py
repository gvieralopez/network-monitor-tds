import logging

__version__ = "0.2.2-beta0"

logging.basicConfig(level=logging.INFO)
logging.getLogger("alembic").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
