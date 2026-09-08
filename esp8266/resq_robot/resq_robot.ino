/*
 * =============================================================================
 * RESQ-NET: ESP-12E / ESP8266 Omni-Directional Robot Firmware (API Connected)
 * =============================================================================
 * Hardware Pin Mapping (Matches User Wiring):
 *   - Motor A (Left Omni)  : mA1 = D5 (GPIO14), mA2 = D6 (GPIO12)
 *   - Motor B (Right Omni) : mB1 = D2 (GPIO4),  mB2 = D3 (GPIO0)
 *   - Motor C (Rear Omni)  : mC1 = D0 (GPIO16), mC2 = D1 (GPIO5)
 * =============================================================================
 */

#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClientSecure.h>
#include <ArduinoJson.h>

// =============================================================================
// 1. WI-FI & PUBLIC BACKEND CONFIGURATION
// =============================================================================
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// Public HTTPS Cloud API Endpoint (Render / Koyeb / Railway)
// Replace with your actual deployed HTTPS URL!
const char* SERVER_URL    = "https://your-resq-net.onrender.com/api/iot/state";

// Motor PWM Speed (0 to 255)
const int MOTOR_SPEED     = 150; 

// =============================================================================
// 2. MOTOR DRIVER PIN MAPPING
// =============================================================================
const int mA1 = D5; // Motor A IN1
const int mA2 = D6; // Motor A IN2

const int mB1 = D2; // Motor B IN1
const int mB2 = D3; // Motor B IN2

const int mC1 = D0; // Motor C IN1 (GPIO16 - Digital only)
const int mC2 = D1; // Motor C IN2

unsigned long lastPollTime = 0;
const unsigned long POLL_INTERVAL = 300; // Poll backend every 300ms
String lastDirection = "";

// Helper function for pin writes (handles D0 digital-only restriction)
void setPin(int pin, int pwmVal) {
  if (pin == D0) {
    digitalWrite(pin, (pwmVal > 0) ? HIGH : LOW);
  } else {
    if (pwmVal == 0) {
      analogWrite(pin, 0);
      digitalWrite(pin, LOW);
    } else {
      analogWrite(pin, pwmVal);
    }
  }
}

// -----------------------------------------------------------------------------
// MOTOR MOVEMENT FUNCTIONS (User exact omni kinematics)
// -----------------------------------------------------------------------------

void stopMotors() {
  setPin(mA1, 0); setPin(mA2, 0);
  setPin(mB1, 0); setPin(mB2, 0);
  setPin(mC1, 0); setPin(mC2, 0);
}

void moveNorth() {
  // A STOP, B BACKWARD, C FORWARD
  setPin(mA1, 0);           setPin(mA2, 0);
  setPin(mB1, 0);           setPin(mB2, MOTOR_SPEED);
  setPin(mC1, MOTOR_SPEED); setPin(mC2, 0);
}

void moveSouth() {
  // A STOP, B FORWARD, C BACKWARD
  setPin(mA1, 0);           setPin(mA2, 0);
  setPin(mB1, MOTOR_SPEED); setPin(mB2, 0);
  setPin(mC1, 0);           setPin(mC2, MOTOR_SPEED);
}

void moveNorthWest() {
  // A BACKWARD, B BACKWARD, C FORWARD
  setPin(mA1, 0);           setPin(mA2, MOTOR_SPEED);
  setPin(mB1, 0);           setPin(mB2, MOTOR_SPEED);
  setPin(mC1, MOTOR_SPEED); setPin(mC2, 0);
}

void moveSouthEast() {
  // A FORWARD, B FORWARD, C BACKWARD
  setPin(mA1, MOTOR_SPEED); setPin(mA2, 0);
  setPin(mB1, MOTOR_SPEED); setPin(mB2, 0);
  setPin(mC1, 0);           setPin(mC2, MOTOR_SPEED);
}

void moveCW() {
  // A FORWARD, B FORWARD, C FORWARD
  setPin(mA1, MOTOR_SPEED); setPin(mA2, 0);
  setPin(mB1, MOTOR_SPEED); setPin(mB2, 0);
  setPin(mC1, MOTOR_SPEED); setPin(mC2, 0);
}

void moveCCW() {
  // A BACKWARD, B BACKWARD, C BACKWARD
  setPin(mA1, 0);           setPin(mA2, MOTOR_SPEED);
  setPin(mB1, 0);           setPin(mB2, MOTOR_SPEED);
  setPin(mC1, 0);           setPin(mC2, MOTOR_SPEED);
}

// -----------------------------------------------------------------------------
// SETUP & LOOP
// -----------------------------------------------------------------------------

void setup() {
  Serial.begin(115200);
  delay(200);

  // Initialize Motor Pins
  pinMode(mA1, OUTPUT); pinMode(mA2, OUTPUT);
  pinMode(mB1, OUTPUT); pinMode(mB2, OUTPUT);
  pinMode(mC1, OUTPUT); pinMode(mC2, OUTPUT);

  stopMotors();

  Serial.println("\n==========================================");
  Serial.println("   RESQ-NET ESP-12E MOTOR CONTROLLER     ");
  Serial.println("==========================================");

  // Boot motor self-test (1 second)
  Serial.println("[TEST] Running 1-second Boot Motor Test...");
  moveCW();
  delay(1000);
  stopMotors();
  Serial.println("[TEST] Boot Motor Test Complete.");

  // Connect to Wi-Fi
  Serial.print("[WIFI] Connecting to: ");
  Serial.println(WIFI_SSID);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 30) {
    delay(500);
    Serial.print(".");
    attempts++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\n[WIFI] Connected Successfully!");
    Serial.print("[WIFI] ESP-12E IP Address: ");
    Serial.println(WiFi.localIP());
    Serial.print("[HTTP] Polling Server URL: ");
    Serial.println(SERVER_URL);
  } else {
    Serial.println("\n[WIFI ERROR] Connection Failed! Check SSID/Password.");
  }
}

void loop() {
  if (millis() - lastPollTime >= POLL_INTERVAL) {
    lastPollTime = millis();

    if (WiFi.status() == WL_CONNECTED) {
      pollBackendAPI();
    } else {
      Serial.println("[WIFI ERROR] Wi-Fi lost! Reconnecting & stopping motors.");
      stopMotors();
      WiFi.reconnect();
    }
  }
}

void pollBackendAPI() {
  WiFiClientSecure client;
  client.setInsecure(); // Bypass SSL fingerprint checking for cloud HTTPS prototypes
  HTTPClient http;

  client.setTimeout(1500);
  http.setTimeout(1500);

  if (!http.begin(client, SERVER_URL)) {
    Serial.println("[HTTP ERROR] Failed to initialize HTTPS connection.");
    stopMotors();
    return;
  }

  int httpCode = http.GET();

  if (httpCode == HTTP_CODE_OK) {
    String payload = http.getString();
    
    bool north = false, south = false, northwest = false, southeast = false, cw = false, ccw = false;
    String active_direction = "STOP";

    // Parse Backend JSON
    StaticJsonDocument<512> doc;
    DeserializationError error = deserializeJson(doc, payload);

    if (!error) {
      north     = doc["north"] | false;
      south     = doc["south"] | false;
      northwest = doc["northwest"] | false;
      southeast = doc["southeast"] | false;
      cw        = doc["cw"] | false;
      ccw       = doc["ccw"] | false;
    } else {
      // Fallback parser if JSON parse error
      String lowerPayload = payload;
      lowerPayload.toLowerCase();
      if      (lowerPayload.indexOf("\"northwest\":true") >= 0) northwest = true;
      else if (lowerPayload.indexOf("\"southeast\":true") >= 0) southeast = true;
      else if (lowerPayload.indexOf("\"north\":true")     >= 0) north     = true;
      else if (lowerPayload.indexOf("\"south\":true")     >= 0) south     = true;
      else if (lowerPayload.indexOf("\"ccw\":true")       >= 0) ccw       = true;
      else if (lowerPayload.indexOf("\"cw\":true")        >= 0) cw        = true;
    }

    executeMovement(north, south, northwest, southeast, cw, ccw);
  } else {
    Serial.print("[HTTP ERROR] Server response code: ");
    Serial.println(httpCode);
    stopMotors();
  }

  http.end();
}

void executeMovement(bool north, bool south, bool northwest, bool southeast, bool cw, bool ccw) {
  String currentDir = "STOP";

  if (north) {
    currentDir = "NORTH";
    moveNorth();
  }
  else if (south) {
    currentDir = "SOUTH";
    moveSouth();
  }
  else if (northwest) {
    currentDir = "NORTHWEST";
    moveNorthWest();
  }
  else if (southeast) {
    currentDir = "SOUTHEAST";
    moveSouthEast();
  }
  else if (cw) {
    currentDir = "CLOCKWISE";
    moveCW();
  }
  else if (ccw) {
    currentDir = "COUNTERCLOCKWISE";
    moveCCW();
  }
  else {
    stopMotors();
  }

  if (currentDir != lastDirection) {
    Serial.print("[ACTION] Direction changed to: ");
    Serial.println(currentDir);
    lastDirection = currentDir;
  }
}
