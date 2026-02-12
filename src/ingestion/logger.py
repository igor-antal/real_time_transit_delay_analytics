import logging
from datetime import datetime


now = datetime.now()
now_string = now.strftime("%Y-%m-%d-%H%M%S")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(filename)s] - %(levelname)s - %(message)s",
    filename=f"ingestion/logs/log_{now_string}.log"
)

logger = logging.getLogger("project_logger")