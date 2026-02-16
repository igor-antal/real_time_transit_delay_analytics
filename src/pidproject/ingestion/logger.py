import logging
from datetime import datetime


now = datetime.now()
now_string = now.strftime("%Y-%m-%d-%H%M%S")
LOGS_ABSOLUTE_PATH = r"C:\Users\jumat\PycharmProject\PIDProject\src\pidproject\ingestion\logs"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(filename)s] - %(levelname)s - %(message)s",
    filename=f"{LOGS_ABSOLUTE_PATH}/log_{now_string}.log"
)

logger = logging.getLogger("project_logger")
