
from flask import Flask, render_template, request, jsonify
import pandas as pd
import numpy as np
import joblib

app = Flask(__name__)

# Load Production Model
MODEL_PATH = "models/production_model.pkl"
try:
    model_data = joblib.load(MODEL_PATH)
    model = model_data["model"]
    FEATURES = model_data["features"]
    CLASSES = model_data["classes"]
    print(f"Production Model loaded. Features: {FEATURES}")
except Exception as e:
    print(f"Error loading production model: {e}")
    model = None
    FEATURES = ["reagent 1 (mo)", "reagent 2 (fecl3)"] # Fallback
    CLASSES = [0, 1]

# Load Production Weights
import json
WEIGHTS = {}
try:
    with open("production_weights.json", "r") as f:
        WEIGHTS = json.load(f)
    print("Production Weights loaded.")
except Exception as e:
    print(f"Warning: Could not load weights. {e}")

@app.route('/')
def home():
    return render_template('index.html', features=FEATURES)

@app.route('/predict', methods=['POST'])
def predict():
    try:
        # Get data from JSON
        data = request.json
        inputs = {}
        for i in range(1, 11):
            inputs[f'r{i}'] = float(data.get(f'r{i}', 0))
        
        return run_prediction(inputs)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

import requests
from PIL import Image
from io import BytesIO
import math
import os

CONFIG_FILE = 'config.json'

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except:
             return {}
    return {}

def save_config(config):
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except Exception as e:
        print(f"Failed to save config: {e}")

@app.route('/get_config', methods=['GET'])
def get_config_route():
    return jsonify(load_config())

@app.route('/test_connection', methods=['POST'])
def test_connection():
    try:
        data = request.json
        camera_url = data.get('camera_url')
        if not camera_url:
            return jsonify({'status': 'error', 'message': 'No URL provided'})
        
        print(f"Testing connection to {camera_url}...")
        resp = requests.get(camera_url, timeout=5)
        
        if resp.status_code == 200:
             # Try to parse generic image size
             try:
                 img = Image.open(BytesIO(resp.content))
                 return jsonify({'status': 'success', 'size': f"{img.size[0]}x{img.size[1]}"})
             except:
                 return jsonify({'status': 'success', 'size': f"{len(resp.content)} bytes (Not an Image?)"})
        else:
            return jsonify({'status': 'error', 'message': f"HTTP {resp.status_code}"})
            
    except Exception as e:
        print(f"Connection test error: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

def get_averaged_rgb(img, x, y, radius=2):
    """Get average RGB within a square radius around (x, y)."""
    width, height = img.size
    r_total, g_total, b_total = 0, 0, 0
    count = 0
    x, y = int(x), int(y)
    for dx in range(-radius, radius + 1):
        for dy in range(-radius, radius + 1):
            nx, ny = x + dx, y + dy
            if 0 <= nx < width and 0 <= ny < height:
                r, g, b = img.getpixel((nx, ny))
                r_total += r
                g_total += g
                b_total += b
                count += 1
    if count == 0: return (0, 0, 0)
    return (r_total / count, g_total / count, b_total / count)

def calculate_delta_rgb(sample, blank):
    return math.sqrt(sum((s - b) ** 2 for s, b in zip(sample, blank)))

@app.route('/analyze_image', methods=['POST'])
def analyze_image():
    try:
        data = request.json
        camera_url = data.get('camera_url')
        coordinates = data.get('coordinates')
        blank_rgb = data.get('blank_rgb', [255, 255, 255])
        
        # Save Config for persistence
        current_config = {
            'camera_url': camera_url,
            'coordinates': coordinates,
            'blank_rgb': blank_rgb
        }
        save_config(current_config)
        
        if not camera_url:
            return jsonify({'status': 'error', 'message': 'Camera URL is required'})
            
        print(f"Fetching image from {camera_url}...")
        try:
            # Simulate "Command" by hitting the URL which likely triggers capture
            resp = requests.get(camera_url, timeout=5)
            img = Image.open(BytesIO(resp.content)).convert('RGB')
        except Exception as err:
             return jsonify({'status': 'error', 'message': f'Failed to fetch image: {err}'})
        
        print(f"Image fetched. Size: {img.size}")
        
        inputs = {}
        extracted_data = {}
        
        for i in range(1, 11):
            key_idx = str(i)
            r_key = f'r{i}'
            
            if coordinates and key_idx in coordinates:
                coords = coordinates[key_idx]
                x = float(coords.get('x', 0))
                y = float(coords.get('y', 0))
                
                sample_rgb = get_averaged_rgb(img, x, y)
                delta = calculate_delta_rgb(sample_rgb, blank_rgb)
                
                inputs[r_key] = delta
                extracted_data[r_key] = {
                    'coords': (x, y),
                    'rgb': [round(x,1) for x in sample_rgb],
                    'delta': round(delta, 2)
                }
            else:
                inputs[r_key] = 0.0
        
        print(f"Extracted Inputs: {inputs}")
        result_response = run_prediction(inputs)
        
        if result_response.status_code == 200:
             json_data = result_response.get_json()
             if json_data['status'] == 'success':
                 json_data['result']['extraction_details'] = extracted_data
                 return jsonify(json_data)
        
        return result_response

    except Exception as e:
        print(f"Error in analyze_image: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

def run_prediction(inputs):
    """
    Core prediction logic.
    inputs: dict like {'r1': 10.5, 'r2': ...}
    """
    try:
        print(f"Running Prediction on: {inputs}")
        input_map = {}
        for i in range(1, 11):
            search_key = f"reagent {i}".lower()
            matched_feature = None
            for f in FEATURES:
                f_norm = f.lower()
                if f_norm == search_key:
                    matched_feature = f
                    break
                if f_norm.startswith(search_key):
                    suffix = f_norm[len(search_key):]
                    if not suffix or not suffix[0].isdigit():
                        matched_feature = f
                        break
            if matched_feature:
                input_map[matched_feature] = inputs[f'r{i}']
        
        df = pd.DataFrame([input_map])
        for f in FEATURES:
            if f not in df.columns:
                df[f] = 0.0
        df = df[FEATURES]
        
        s_score = 0.0
        for w_key, w_val in WEIGHTS.items():
            if w_key in input_map:
                s_score += w_val * input_map[w_key]
        
        if model:
            pred_intensities = model.predict(df)[0]
            result_map = {str(taste): float(val) for taste, val in zip(CLASSES, pred_intensities)}
            dominant_taste = max(result_map, key=result_map.get)
            confidence = result_map[dominant_taste]

            active_tastes = []
            for taste, score in result_map.items():
                if score > 0.15: 
                     active_tastes.append({"name": taste, "score": score})
            active_tastes.sort(key=lambda x: x["score"], reverse=True)
            
            if len(active_tastes) == 0:
                prediction_display = "No Distinct Taste"
            elif len(active_tastes) == 1:
                t_name = active_tastes[0]['name']
                t_score = active_tastes[0]['score']
                if t_score < 0.6:
                    prediction_display = f"Mild {t_name}"
                else:
                    prediction_display = t_name
            else:
                names = []
                for t in active_tastes:
                    prefix = "Mild " if t['score'] < 0.6 else ""
                    names.append(f"{prefix}{t['name']}")
                prediction_display = " + ".join(names)
            
            result = {
                "predicted_taste": prediction_display,
                "confidence": float(confidence), 
                "all_probabilities": result_map, 
                "detected_tastes_count": len(active_tastes),
                "active_tastes": active_tastes,
                "signal_score": round(s_score, 2)
            }
            return jsonify({'status': 'success', 'result': result})
        else:
            return jsonify({'status': 'error', 'message': 'Model not loaded.'})
    except Exception as e:
        print(f"Prediction logic error: {e}")
        return jsonify({'status': 'error', 'message': str(e)})

# Hack to avoid import error in predict
from_mock_generation = False

if __name__ == '__main__':
    app.run(debug=True, port=5000)
