#include <WiFiManager.h> // Library: WiFiManager by tzapu
#include <Firebase_ESP_Client.h> // Library: Firebase Arduino Client Library for ESP8266 and ESP32 by Mobizt
#include "esp_camera.h"
#include "soc/soc.h"           // Disable brownout problems
#include "soc/rtc_cntl_reg.h"  // Disable brownout problems

// --- 1. USER CONFIGURATION ---

// ⚠️ YOUR CREDENTIALS ⚠️
#define API_KEY "AIzaSyBSA77EQhqic4J5xV4KsfzvFzk7Ae7MiLw" 
#define DATABASE_URL "palateonics-default-rtdb.asia-southeast1.firebasedatabase.app"

// ⚠️ EXTERNAL LED PINS ⚠️
// Updated to use GPIO 14 and 15
#define LED_PIN_1  14 
#define LED_PIN_2  15 

// --- CALIBRATED COORDINATES ---
// Update these numbers once you have your final setup!
struct Point { int x; int y; };
Point spots[6] = { 
  {100, 120}, // 1. Sour
  {200, 120}, // 2. Sweet
  {300, 120}, // 3. Salty
  {100, 240}, // 4. Potency
  {200, 240}, // 5. Pungent
  {300, 240}  // 6. Purity
};
String labels[6] = {"Sour", "Sweet", "Salty", "Potency", "Pungent", "Purity"};

// --- 2. SYSTEM OBJECTS ---
FirebaseData fbDO;
FirebaseAuth auth;
FirebaseConfig config;

// HEARTBEAT TRACKING
unsigned long lastHeartbeat = 0;
const unsigned long HEARTBEAT_INTERVAL = 10000; // Update every 10 seconds

// CAMERA PINS (AI THINKER)
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

void setup() {
  WRITE_PERI_REG(RTC_CNTL_BROWN_OUT_REG, 0); // Disable brownout
  Serial.begin(115200);

  // --- INIT LEDS ---
  pinMode(LED_PIN_1, OUTPUT);
  pinMode(LED_PIN_2, OUTPUT);
  digitalWrite(LED_PIN_1, LOW); // Ensure off
  digitalWrite(LED_PIN_2, LOW); // Ensure off

  // --- 1. INIT CAMERA FIRST (Priority for RAM) ---
  camera_config_t config_cam;
  config_cam.ledc_channel = LEDC_CHANNEL_0;
  config_cam.ledc_timer = LEDC_TIMER_0;
  config_cam.pin_d0 = Y2_GPIO_NUM;
  config_cam.pin_d1 = Y3_GPIO_NUM;
  config_cam.pin_d2 = Y4_GPIO_NUM;
  config_cam.pin_d3 = Y5_GPIO_NUM;
  config_cam.pin_d4 = Y6_GPIO_NUM;
  config_cam.pin_d5 = Y7_GPIO_NUM;
  config_cam.pin_d6 = Y8_GPIO_NUM;
  config_cam.pin_d7 = Y9_GPIO_NUM;
  config_cam.pin_xclk = XCLK_GPIO_NUM;
  config_cam.pin_pclk = PCLK_GPIO_NUM;
  config_cam.pin_vsync = VSYNC_GPIO_NUM;
  config_cam.pin_href = HREF_GPIO_NUM;
  config_cam.pin_sscb_sda = SIOD_GPIO_NUM;
  config_cam.pin_sscb_scl = SIOC_GPIO_NUM;
  config_cam.pin_pwdn = PWDN_GPIO_NUM;
  config_cam.pin_reset = RESET_GPIO_NUM;
  config_cam.xclk_freq_hz = 20000000;
  config_cam.pixel_format = PIXFORMAT_RGB565; 
  config_cam.frame_size = FRAMESIZE_QVGA; 
  config_cam.fb_count = 1; // Keep frame buffer count low!
  
  if (esp_camera_init(&config_cam) != ESP_OK) {
    Serial.println("❌ Camera Fail"); return;
  }
  Serial.println("✅ Camera Ready!");

  // --- 2. WIFI MANAGER ---
  WiFiManager wm;
  bool res = wm.autoConnect("E-Tongue Setup"); 

  if(!res) {
    Serial.println("Failed to connect");
    ESP.restart();
  } 
  else {
    Serial.println("✅ WiFi Connected via WiFiManager!");
  }

  // --- 3. FIREBASE INIT ---
  config.api_key = API_KEY;
  config.database_url = DATABASE_URL;
  config.signer.test_mode = true; 
  
  Firebase.begin(&config, &auth);
  fbDO.setBSSLBufferSize(4096, 1024); 
  Firebase.reconnectWiFi(true);
  Serial.println("✅ Firebase Initialized.");
  
  // --- 4. SYNC TIME ---
  configTime(0, 0, "pool.ntp.org", "time.nist.gov");
  
  updateHeartbeat();
}

void loop() {
  if (Firebase.ready()) {
    
    // UPDATE HEARTBEAT
    unsigned long currentMillis = millis();
    if (currentMillis - lastHeartbeat >= HEARTBEAT_INTERVAL) {
      updateHeartbeat();
      lastHeartbeat = currentMillis;
    }
    
    // LISTEN FOR "SCAN" COMMAND
    if (Firebase.RTDB.getString(&fbDO, "/Control/Status")) {
       String status = fbDO.stringData();
       
       if (status == "SCAN") {
          Serial.println("🚀 APP COMMAND RECEIVED! Analyzing...");
          
          if (analyze_and_upload()) {
            Firebase.RTDB.setString(&fbDO, "/Control/Status", "IDLE");
            Serial.println("✅ Analysis Complete.");
          } else {
             Serial.println("❌ Capture Failed");
          }
       }
    }
  }
  delay(500); 
}

void updateHeartbeat() {
  unsigned long long timestamp = (unsigned long long)time(nullptr) * 1000ULL;
  if (timestamp < 1000000000000ULL) timestamp = 1700000000000ULL; 
  
  Firebase.RTDB.setDouble(&fbDO, "/Device/LastSeen", (double)timestamp);
}

bool analyze_and_upload() {
  // 1. TURN ON LIGHTS BEFORE CAPTURE
  digitalWrite(LED_PIN_1, HIGH);
  digitalWrite(LED_PIN_2, HIGH);
  Serial.println("💡 LEDs ON - Starting capture...");
  delay(200); // Allow sensor to adjust to new light level
  
  camera_fb_t * fb = esp_camera_fb_get();
  
  if (!fb) {
    // Turn off LEDs even if capture fails
    digitalWrite(LED_PIN_1, LOW);
    digitalWrite(LED_PIN_2, LOW);
    Serial.println("💡 LEDs OFF - Capture failed");
    return false;
  }

  FirebaseJson jsonLive;    

  for (int i=0; i<6; i++) {
    int cx = spots[i].x;
    int cy = spots[i].y;
    long r_tot=0, g_tot=0, b_tot=0;
    int count = 0;
    
    int radius = 8; 
    int radius_sq = radius * radius;

    for (int y = cy - radius; y < cy + radius; y++) {
      for (int x = cx - radius; x < cx + radius; x++) {
        int dx = x - cx;
        int dy = y - cy;
        if (dx*dx + dy*dy > radius_sq) continue; 
        
        int idx = (y * 320 + x) * 2;
        if(idx < 0 || idx >= fb->len) continue;
        
        uint16_t p = (fb->buf[idx] << 8) | fb->buf[idx+1];
        int r_val = ((p >> 11) & 0x1F) * 255 / 31;
        int g_val = ((p >> 5) & 0x3F) * 255 / 63;
        int b_val = (p & 0x1F) * 255 / 31;

        r_tot += r_val; g_tot += g_val; b_tot += b_val;
        count++;
      }
    }
    
    if(count == 0) count = 1;
    int r = r_tot/count; int g = g_tot/count; int b = b_tot/count;
    
    // HSV Conversion
    float rn = r/255.0; float gn = g/255.0; float bn = b/255.0;
    float cmax = max(rn, max(gn, bn)); float cmin = min(rn, min(gn, bn));
    float diff = cmax - cmin;
    
    int h = 0;
    if(diff==0) h=0;
    else if(cmax==rn) h=(int)(60*((gn-bn)/diff)+360)%360;
    else if(cmax==gn) h=(int)(60*((bn-rn)/diff)+120)%360;
    else if(cmax==bn) h=(int)(60*((rn-gn)/diff)+240)%360;
    
    int s = (cmax==0) ? 0 : (diff/cmax)*255;
    int v = cmax*255;

    String label = labels[i];
    
    // Live Data
    jsonLive.set(label + "/R", r);
    jsonLive.set(label + "/G", g);
    jsonLive.set(label + "/B", b);
    jsonLive.set(label + "/H", h);
    jsonLive.set(label + "/S", s);
    jsonLive.set(label + "/V", v);
    
    Serial.printf("%s -> S:%d\n", label.c_str(), s);
  }
  
  esp_camera_fb_return(fb);

  // --- UPLOAD ONLY SENSOR DATA ---
  // The Flutter App will handle the History entry
  Serial.println("Uploading Live View...");
  Firebase.RTDB.updateNode(&fbDO, "/SensorData", &jsonLive);

  // 2. TURN OFF LIGHTS AFTER CAPTURE AND UPLOAD COMPLETE
  digitalWrite(LED_PIN_1, LOW);
  digitalWrite(LED_PIN_2, LOW);
  Serial.println("💡 LEDs OFF - Capture complete");

  return true;
}