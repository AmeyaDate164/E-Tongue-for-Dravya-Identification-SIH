# Standard Operating Procedure (SOP) - Taste AI System

## 1. System Overview
The **Taste AI** system is a sensor fusion platform that predicts taste profiles (Sour, Sweet, Bitter, etc.) by analyzing colorimetric reactions of 10 specific reagents. It uses an **ESP32-CAM** to capture images of the reagent array, extracts RGB values, calculates the Euclidean Delta against a blank reference, and feeds this data into a Machine Learning model.

## 2. Prerequisites
- **Hardware**:
    - Laptop/PC running the Flask Server.
    - ESP32-CAM module flashed with the image capture firmware.
    - Reagent Array (Microfluidic chip or testing plate) with 10 spots.
    - WiFi Connection (Both Laptop and ESP32 must be on the same network).
- **Software**:
    - Python 3.8+
    - Dependencies: `flask`, `pandas`, `numpy`, `joblib`, `Pillow`, `requests` (Install via `pip install -r requirements.txt` if available, or manually).

## 3. Startup Procedure
1.  **Power on the ESP32**: Connect it to a power source. Ensure it connects to the WiFi.
    *   *Note*: Verify the IP address assigned to the ESP32 (e.g., via Serial Monitor or Router).
2.  **Start the Server**:
    *   Open a terminal in the project folder: `SIH25/final model`
    *   Run the application:
        ```bash
        python app.py
        ```
    *   Wait for the message: `* Running on http://127.0.0.1:5000`
3.  **Access the Dashboard**:
    *   Open Google Chrome or any modern browser.
    *   Navigate to: [http://localhost:5000](http://localhost:5000)

## 4. Configuration (One-Time Setup)
Upon first launch, you must configure the computer vision system:

1.  Click the **"Camera Analysis"** tab.
2.  **Camera Stream URL**: Enter the endpoint where the ESP32 serves the still image.
    *   *Example*: `http://192.168.43.203/capture` (Replace IP with your actual ESP32 IP).
3.  **Blank Reference RGB**:
    *   Place a "Blank" sample (water/neutral buffer) under the camera.
    *   Enter the RGB values (e.g., 255, 255, 255) to be used as the baseline for 0 reaction.
4.  **Reagent Coordinates**:
    *   You need to tell the system where to look for each of the 10 reagents.
    *   Enter the **X** and **Y** pixel coordinates for Reagents 1 through 10.
    *   *Tip*: You can take a snapshot image and use MS Paint or an online image coordinator tool to find the exact X/Y of the center of each spot.
5.  **Save**: These settings are automatically saved to `config.json` when you run an analysis.

## 5. Operation Modes

### Mode A: Single Scan (Manual Trigger)
Use this when testing specific individual samples.
1.  Place the sample container under the camera.
2.  Click **"Start Auto Analysis"**.
3.  The system will:
    *   Capture one image.
    *   Process the 10 spots.
    *   Display the **Predicted Taste**, **Confidence**, and **Radar Chart**.
    *   Wait for the next command.

### Mode B: Continuous Only (Auto-Pilot)
Use this for rapid testing of multiple samples without touching the PC.
1.  In the "Camera Analysis" tab, check the box **"Continuous Mode (Auto-Refresh)"**.
2.  Set the **Interval** (default is 5 seconds). Ensure this gives you enough time to swap samples.
3.  Click **"Start Auto Analysis"**.
4.  **Workflow**:
    *   The system scans immediately.
    *   It then waits for the interval.
    *   It scans again automatically.
5.  **To Stop**: Click the red **"Stop"** button that appears.

## 6. Troubleshooting
| Issue | Potential Cause | Solution |
| :--- | :--- | :--- |
| **"Failed to fetch image"** | ESP32 is off or IP is wrong. | Check ESP32 power. Ping the IP in a new tab to see if it loads. |
| **"No Distinct Taste"** | Delta RGB values are too low. | Check lighting conditions. Ensure the "Blank RGB" reference is accurate. |
| **Wrong Prediction** | Coordinates are misaligned. | Re-check X/Y coordinates. Ensure the camera position hasn't shifted. |
| **System freezes** | Network timeout. | Stop the server (`Ctrl+C`) and restart `python app.py`. |

## 7. Next Steps & Recommendations
1.  **Calibration Utility**: Build a small tool to visually click on the camera feed to set coordinates instead of typing X/Y numbers manually.
2.  **Lighting Control**: Standardize the lighting (e.g., an LED ring) to ensure color consistency, as RGB values drift significantly with ambient light changes.
3.  **Model Retraining**: As you collect real-world data, save the successful scans to a CSV and re-train the model to improve accuracy over time.
4.  **Mobile Access**: Since it's a Web App, you can access `http://<YOUR_PC_IP>:5000` from your phone if it's on the same WiFi, allowing you to control the system while standing next to the sensor.
