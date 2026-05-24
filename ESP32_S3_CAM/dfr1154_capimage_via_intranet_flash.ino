#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include <DFRobot_LTR308.h>

// ---- CONFIG ----
const char* WIFI_SSID     = "XXXX";
const char* WIFI_PASSWORD = "XXXX";
const char* SERVER_URL    = "http://XXXX/upload";
const int   INTERVAL_MS   = 5000;
// ----------------

#define IR_LED_PIN 3

// DFR1154 pin definitions
#define PWDN_GPIO_NUM  -1
#define RESET_GPIO_NUM -1
#define XCLK_GPIO_NUM   5
#define Y9_GPIO_NUM     4
#define Y8_GPIO_NUM     6
#define Y7_GPIO_NUM     7
#define Y6_GPIO_NUM    14
#define Y5_GPIO_NUM    17
#define Y4_GPIO_NUM    21
#define Y3_GPIO_NUM    18
#define Y2_GPIO_NUM    16
#define VSYNC_GPIO_NUM  1
#define HREF_GPIO_NUM   2
#define PCLK_GPIO_NUM  15
#define SIOD_GPIO_NUM   8
#define SIOC_GPIO_NUM   9

DFRobot_LTR308 light;

void initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 10000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size   = FRAMESIZE_UXGA;
  config.fb_location  = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 3;
  config.fb_count     = 1;
  config.grab_mode    = CAMERA_GRAB_LATEST;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x\n", err);
    while (true) delay(1000);
  }

  sensor_t* s = esp_camera_sensor_get();
  s->set_framesize(s, FRAMESIZE_UXGA);
  s->set_saturation(s, 2); 
  Serial.printf("Camera PID: 0x%x\n", s->id.PID);

  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);
    s->set_brightness(s, 1);
    s->set_saturation(s, -2);
  }

  Serial.println("Camera ready");
}

void applySensorSettings(bool irMode) {
  sensor_t* s = esp_camera_sensor_get();
  if (!s) return;

  if (irMode) {
    s->set_brightness(s, 2);
    s->set_contrast(s, 2);
    s->set_saturation(s, -2);
    // removed set_special_effect — register unsupported on this sensor revision

    if (s->id.PID == OV3660_PID) {
      s->set_gain_ctrl(s, 0);
      s->set_agc_gain(s, 20);
      s->set_aec_value(s, 800);
    } else {
      s->set_gain_ctrl(s, 0);
      s->set_ae_level(s, 2);
    }
  } else {
    s->set_brightness(s, 1);
    s->set_contrast(s, 0);
    s->set_saturation(s, 0);
    // removed set_special_effect
    s->set_gain_ctrl(s, 1);
    s->set_ae_level(s, 0);

    if (s->id.PID == OV3660_PID) {
      s->set_agc_gain(s, 0);
      s->set_aec_value(s, 300);
    }
  }
}

void flushFrameBuffer() {
  camera_fb_t* stale = esp_camera_fb_get();
  if (stale) esp_camera_fb_return(stale);
}

void sendImage(camera_fb_t* fb, const char* label) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected, skipping frame");
    return;
  }

  String url = String(SERVER_URL) + "?type=" + label;

  HTTPClient http;
  http.begin(url);
  http.addHeader("Content-Type", "image/jpeg");

  int httpCode = http.POST(fb->buf, fb->len);
  if (httpCode > 0) {
    Serial.printf("[%s] Sent %u bytes, HTTP %d\n", label, fb->len, httpCode);
  } else {
    Serial.printf("[%s] POST failed: %s\n", label, http.errorToString(httpCode).c_str());
  }
  http.end();
}

void captureAndSend() {
  // --- Normal image (IR LED off) ---
  digitalWrite(IR_LED_PIN, LOW);
  delay(200);
  flushFrameBuffer();
  camera_fb_t* fb_normal = esp_camera_fb_get();
  if (fb_normal) {
    sendImage(fb_normal, "normal");
    esp_camera_fb_return(fb_normal);
  }

  // --- IR image (IR LED on) ---
  digitalWrite(IR_LED_PIN, HIGH);
  delay(1500);
  flushFrameBuffer();
  camera_fb_t* fb_ir = esp_camera_fb_get();
  if (fb_ir) {
    sendImage(fb_ir, "ir");
    esp_camera_fb_return(fb_ir);
  }

  digitalWrite(IR_LED_PIN, LOW);
}

void setup() {
  Serial.begin(115200);
  delay(3000);

  pinMode(IR_LED_PIN, OUTPUT);
  digitalWrite(IR_LED_PIN, LOW);

  initCamera();

  while (!light.begin()) {
    Serial.println("LTR308 init failed, retrying...");
    delay(1000);
  }
  Serial.println("LTR308 ready");

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nConnected! IP: " + WiFi.localIP().toString());
}

void loop() {
  uint32_t data = light.getData();
  Serial.printf("Light: %u lux\n", light.getLux(data));

  captureAndSend();

  delay(INTERVAL_MS);
}