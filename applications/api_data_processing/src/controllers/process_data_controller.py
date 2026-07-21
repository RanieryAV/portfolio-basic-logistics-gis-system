import os
import traceback
import logging
from flask import Blueprint, request, jsonify
from flasgger import swag_from
from os import path
from dotenv import load_dotenv
from ..services.process_data_service import ProcessDataService
from domain.config.data_processing.spark_session_initializer import SparkSessionInitializer
import glob

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

@preprocess_data_bp.route('/process-raw-data', methods=['POST'])
@swag_from(path.join(path.dirname(__file__), '../docs/process_raw_data_post.yml'))
def post_process_raw_data():
    # TODO: Implement the logic to process raw data from external interactive sources
    print("TODO: Implement the logic to process raw data from external interactive sources")
