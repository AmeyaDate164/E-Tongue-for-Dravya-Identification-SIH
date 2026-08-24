# E-Tongue for Dravya Identification (SIH)

A smart taste-analysis system that combines colorimetric reagent sensing with computer vision and machine learning to identify dravya/taste characteristics.

## Overview

This project captures an image of a reagent array using an ESP32-CAM, extracts RGB-based reaction features, and predicts taste profiles using a trained machine learning model. The system includes a Flask-based dashboard for analysis and visualization.

## System components
- ESP32-CAM based image acquisition
- Reagent image processing and feature extraction
- Machine learning classification for taste profile prediction
- Web dashboard for interaction and visualization
- SOP document for operation and deployment

## Repository structure

- `src/` - Python application, training code, and dashboard assets
- `src/templates/` - frontend HTML templates
- `src/static/` - CSS and JavaScript assets
- `src/models/` - trained model artifacts
- `firmware/` - ESP32 camera firmware
- `docs/` - project documentation and SOP

## Quick start

```bash
cd src
pip install flask pandas numpy joblib pillow requests
python app.py
```

Then open:

```text
http://localhost:5000
```

## Main files

- `src/app.py` - main Flask application and prediction logic
- `src/data_loader.py` - dataset loading utilities
- `src/model_trainer.py` - model training pipeline
- `src/train_production.py` - production training workflow
- `src/validate_real_data.py` - validation on real-world data
- `src/verify_production.py` - production verification checks
- `src/manual_predict.py` - manual prediction helper
- `src/visualizer.py` - visualization utilities
- `firmware/ESP32_Camera_Taste_Reader.ino` - ESP32 camera capture firmware
- `docs/SOP_Taste_AI.md` - operating procedure and usage guide

## Notes

This folder is intentionally cleaned for GitHub presentation and excludes local runtime data, backup experiments, and generated build artifacts.
