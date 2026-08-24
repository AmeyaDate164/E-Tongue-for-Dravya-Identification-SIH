import pandas as pd
import numpy as np
import pickle
import joblib 
import os
from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

class TasteModel:
    def __init__(self):
        # We use MultiOutputRegressor to predict intensity for each taste independently
        self.model = MultiOutputRegressor(RandomForestRegressor(n_estimators=100, random_state=42))
        self.feature_names = None
        self.target_names = None

    def train(self, X, y):
        """
        Trains the model.
        X: DataFrame of Features
        y: DataFrame of Targets (Columns = Tastes, Values = 0-1)
        """
        self.feature_names = X.columns.tolist()
        self.target_names = y.columns.tolist()
        
        # Split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Fit
        print("Training Multi-Output Regressor...")
        self.model.fit(X_train, y_train)
        
        # Evaluate
        preds = self.model.predict(X_test)
        
        # Calculate R2 Score (Average across all outputs)
        score = self.model.score(X_test, y_test)
        print(f"Model R2 Score: {score:.4f}")
        
        # RMSE
        mse = mean_squared_error(y_test, preds)
        print(f"Mean Squared Error: {mse:.4f}")
        
        return score

    def predict(self, input_data):
        """
        Predicts taste intensity for new data.
        input_data: DataFrame or Dict matching feature columns
        """
        # Ensure input has all columns
        if isinstance(input_data, dict):
            input_df = pd.DataFrame([input_data])
        elif isinstance(input_data, pd.Series):
            input_df = pd.DataFrame([input_data])
        else:
            input_df = input_data.copy()
            
        # Re-index to match training columns (fill missing with 0)
        input_df = input_df.reindex(columns=self.feature_names, fill_value=0)
        
        # Predict Intensities
        # Returns shape (n_samples, n_targets)
        pred_intensities = self.model.predict(input_df)[0]
        
        # Construct Result Dictionary
        result = {taste: float(val) for taste, val in zip(self.target_names, pred_intensities)}
        
        # Determine Dominant Taste (Highest Intensity)
        dominant_taste = max(result, key=result.get)
        dominant_score = result[dominant_taste]
        
        if dominant_score < 0.1:
            dominant_taste = "No Distinct Taste"
            
        return {
            "predicted_taste": dominant_taste, # Backward compat
            "confidence": dominant_score,      # Backward compat
            "all_probabilities": result        # Actually intensities now
        }

    def save(self, directory="models"):
        if not os.path.exists(directory):
            os.makedirs(directory)
            
        path = os.path.join(directory, "taste_model.pkl")
        with open(path, "wb") as f:
            pickle.dump(self, f)
        print(f"Model saved to {path}")

    def save_production_format(self, directory="models"):
        """Saves for Flask App"""
        if not os.path.exists(directory):
            os.makedirs(directory)
            
        path = os.path.join(directory, "production_model.pkl")
        data = {
            "model": self.model,
            "features": self.feature_names,
            "classes": self.target_names # We re-use 'classes' key for compatibility, but it holds Taste Names
        }
        with open(path, "wb") as f:
            joblib.dump(data, f)
        print(f"Production Model saved to {path}")

    @staticmethod
    def load(path="models/taste_model.pkl"):
        with open(path, "rb") as f:
            return pickle.load(f)

if __name__ == "__main__":
    pass
