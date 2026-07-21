from flask import Blueprint, request, jsonify, current_app
from flasgger import swag_from
from os import path
from ..services.prediction_service import PredictionService
#from domain.config.data_processing.spark_session_initializer import SparkSessionInitializer
import traceback
import logging
import numpy as np
import pandas as pd
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

prediction_bp = Blueprint('prediction_bp', __name__)

# Load environment variables
load_dotenv()

@prediction_bp.route('/predict-anomaly', methods=['POST'])
@swag_from(path.join(path.dirname(__file__), '../docs/predict_anomaly.yml'))
def predict_anomaly():
    """
    TO DO: Implement the anomaly prediction logic.
    """
    print("TO DO: Implement the anomaly prediction logic.")
