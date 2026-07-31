import logging

from dotenv import load_dotenv
from flask import Blueprint

# Image libs (Pillow). Shapely optional but recommended.
try:
    SHAPELY_AVAILABLE = True
except Exception:
    SHAPELY_AVAILABLE = False


preprocess_data_bp = Blueprint('process_data_bp', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_logger(name=__name__):
    log = logging.getLogger(name)
    log.setLevel(logging.INFO)
    if not log.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(fmt)
        log.addHandler(ch)
    return log

logger = get_logger()

# Load environment variables
load_dotenv()

class ProcessDataService:
    @staticmethod
    def process_anomaly_data(start_date, end_date):
        """
        TO DO: Process anomaly data
        """
        print("TODO: Implement the logic to process anomaly data")
