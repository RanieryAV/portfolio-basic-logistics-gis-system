import os
import socket
import logging
from datetime import datetime
from pyspark.sql import functions as F
from pyspark.sql import types as T
from pyspark.sql import functions as F
from pyspark.sql import SparkSession

logger = logging.getLogger(__name__)
class PredictionService:

    @staticmethod
    def classify_anomaly(start_date, end_date):
        """
        TO DO: Classify anomaly by calling a logged (already trained) Machine Learning model.
        """
        print("TODO: Implement the logic to classify anomaly by calling a logged (already trained) Machine Learning model")
