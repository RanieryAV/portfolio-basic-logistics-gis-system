from flask import Blueprint, request, jsonify, current_app
from flasgger import swag_from
from os import path
import traceback
from datetime import datetime
import logging
from dotenv import load_dotenv
import tensorflow as tf

training_bp = Blueprint('model_controller', __name__, url_prefix='/models')

# Load environment variables
load_dotenv()

@training_bp.route('/anomaly', methods=['POST'])
@swag_from(path.join(path.dirname(__file__), '../docs/anomaly_training.yml'))
def train_anomaly_model():
    """
    TO DO: Implement the logic for training the anomaly model.
    """
    print("TO DO: Implement the logic for training the anomaly model.")
    
