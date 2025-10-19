from typing import Dict, Any
import logging
import numpy as np
import json
import time
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.preprocessing import StandardScaler
import os

# Local imports
from .database import db_pool, DatabaseError
from .exceptions import FileIOError

class LearningLoop:
    """Lightweight learning loop for policy optimization"""
    
    def __init__(self, db_path: str = "data/core.db"):
        self.logger = logging.getLogger(__name__)
        self.train_count = 0
        self.logger.info("Initializing Learning Loop")
        
        # Database path
        self.db_path = os.path.join(os.path.dirname(__file__), "..", db_path)
        
        # Models
        self.classifier = LogisticRegression()
        self.regressor = Ridge()
        self.scaler = StandardScaler()
        
        # Model status
        self.is_trained = False
        
    def load_training_data(self) -> tuple:
        """Load training data from database"""
        start_time = time.time()
        try:
            with db_pool.connection() as conn:
                # Load training examples
                examples = conn.execute("SELECT * FROM train_examples").fetchall()
                
                if not examples:
                    load_time = time.time() - start_time
                    self.logger.info("No training data found", extra={
                        "event": "no_training_data",
                        "load_time_ms": round(load_time * 1000, 2)
                    })
                    return [], [], []
            
                # Extract features and labels
                features = []
                labels_success = []
                labels_latency = []
                
                for example in examples:
                    # Parse feature JSON
                    try:
                        feature_data = json.loads(example['feature_json'])
                        features.append(list(feature_data.values()))
                        labels_success.append(example['label_success'])
                        labels_latency.append(example['label_latency_ms'])
                    except json.JSONDecodeError as e:
                        self.logger.warning("Failed to parse feature JSON", extra={
                            "event": "feature_json_parse_error",
                            "error": str(e),
                            "example_id": example['id']
                        })
                
                load_time = time.time() - start_time
                self.logger.info("Training data loaded successfully", extra={
                    "event": "training_data_loaded",
                    "sample_count": len(features),
                    "load_time_ms": round(load_time * 1000, 2)
                })
                
                return features, labels_success, labels_latency
        except DatabaseError as e:
            load_time = time.time() - start_time
            self.logger.error("Failed to load training data due to database error", extra={
                "event": "training_data_load_failed",
                "error": str(e),
                "error_type": "database",
                "load_time_ms": round(load_time * 1000, 2)
            })
            return [], [], []
        except Exception as e:
            load_time = time.time() - start_time
            self.logger.error("Failed to load training data due to unexpected error", extra={
                "event": "training_data_load_failed",
                "error": str(e),
                "error_type": "unexpected",
                "load_time_ms": round(load_time * 1000, 2)
            })
            return [], [], []
            
    def train_model(self) -> Dict[str, Any]:
        """Train the lightweight model"""
        start_time = time.time()
        self.train_count += 1
        
        self.logger.info("Starting model training", extra={
            "event": "model_training_start",
            "train_count": self.train_count
        })
        
        # Load training data
        features, labels_success, labels_latency = self.load_training_data()
        
        if not features:
            train_time = time.time() - start_time
            result = {
                "status": "no_data",
                "message": "No training data available"
            }
            self.logger.info("Model training completed - no data", extra={
                "event": "model_training_completed",
                "status": "no_data",
                "train_time_ms": round(train_time * 1000, 2),
                "train_count": self.train_count
            })
            return result
        
        self.logger.info("Training model with samples", extra={
            "event": "model_training_samples",
            "samples": len(features)
        })
        
        try:
            # Convert to numpy arrays
            X = np.array(features)
            y_success = np.array(labels_success)
            y_latency = np.array(labels_latency)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train classifier
            self.classifier.fit(X_scaled, y_success)
            
            # Train regressor
            self.regressor.fit(X_scaled, y_latency)
            
            # Mark as trained
            self.is_trained = True
            
            train_time = time.time() - start_time
            result = {
                "status": "trained",
                "samples": len(features),
                "model_info": {
                    "classifier": str(self.classifier),
                    "regressor": str(self.regressor)
                }
            }
            
            self.logger.info("Model training completed successfully", extra={
                "event": "model_training_completed",
                "status": "trained",
                "samples": len(features),
                "train_time_ms": round(train_time * 1000, 2),
                "train_count": self.train_count
            })
            
            return result
        except Exception as e:
            train_time = time.time() - start_time
            self.logger.error("Failed to train model", extra={
                "event": "model_training_failed",
                "error": str(e),
                "train_time_ms": round(train_time * 1000, 2),
                "train_count": self.train_count
            })
            return {
                "status": "error",
                "error": str(e)
            }
            
    def predict_success(self, features: list) -> float:
        """Predict success probability for given features"""
        if not self.is_trained:
            # Return default probability if not trained
            self.logger.debug("Using default success probability - model not trained", extra={
                "event": "default_success_probability",
                "value": 0.5
            })
            return 0.5
            
        try:
            X = np.array([features])
            X_scaled = self.scaler.transform(X)
            prob = self.classifier.predict_proba(X_scaled)[0][1]  # Probability of success
            self.logger.debug("Success probability predicted", extra={
                "event": "success_probability_predicted",
                "value": prob
            })
            return prob
        except Exception as e:
            self.logger.error("Failed to predict success", extra={
                "event": "success_prediction_failed",
                "error": str(e)
            })
            return 0.5
            
    def predict_latency(self, features: list) -> float:
        """Predict latency for given features"""
        if not self.is_trained:
            # Return default latency if not trained
            self.logger.debug("Using default latency - model not trained", extra={
                "event": "default_latency",
                "value": 1000.0
            })
            return 1000.0
            
        try:
            X = np.array([features])
            X_scaled = self.scaler.transform(X)
            latency = self.regressor.predict(X_scaled)[0]
            self.logger.debug("Latency predicted", extra={
                "event": "latency_predicted",
                "value": latency
            })
            return latency
        except Exception as e:
            self.logger.error("Failed to predict latency", extra={
                "event": "latency_prediction_failed",
                "error": str(e)
            })
            return 1000.0
            
    def get_learning_info(self) -> Dict[str, Any]:
        """Get information about the learning loop for monitoring"""
        return {
            "train_count": self.train_count,
            "is_trained": self.is_trained
        }

if __name__ == "__main__":
    # For testing purposes
    learning_loop = LearningLoop()
    result = learning_loop.train_model()
    print(result)
    
    # Test predictions
    if learning_loop.is_trained:
        test_features = [1, 2, 3, 4, 5]  # Example features
        success_prob = learning_loop.predict_success(test_features)
        latency = learning_loop.predict_latency(test_features)
        print(f"Success probability: {success_prob}")
        print(f"Predicted latency: {latency}")