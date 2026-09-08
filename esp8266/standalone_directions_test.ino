/*
 * =============================================================================
 * RESQ-NET: ESP-12E Isolated Direction & Motor Test (NO WI-FI / NO API)
 * =============================================================================
 * Hardware Pin Mapping (L293D / L298N Motor Driver):
 *   - Motor A (Left Omni Wheel)  : IN1 = D5 (GPIO14), IN2 = D6 (GPIO12)
 *   - Motor B (Right Omni Wheel) : IN1 = D3 (GPIO0),  IN2 = D4 (GPIO2)
 *   - Motor C (Rear Omni Wheel)  : IN1 = D0 (GPIO16), IN2 = D1 (GPIO5)
 * 
 * Description:
 *   Cycles through all 6 movement directions (NORTH, SOUTH, NORTHWEST, 
 *   SOUTHEAST, CW, CCW) for 3 seconds each, with a 2-second STOP pause between.
 *   NO Wi-Fi or API needed — strictly standalone hardware test.
 * =============================================================================
 */

#include <Arduino.h>

// PWM Speed (0 to 255)
const int MOTOR_SPEED = 150;

// Motor A (Left Omni Wheel)
const int MOTOR_A_IN1 = D5;
const int MOTOR_A_IN2 = D6;

// Motor B (Right Omni Wheel)
const int MOTOR_B_IN1 = D3;
const int MOTOR_B_IN2 = D4;

// Motor C (Rear Omni Wheel)
const int MOTOR_C_IN1 = D0;
const int MOTOR_C_IN2 = D1;

void stopMotors() {
  digitalWrite(MOTOR_A_IN1, LOW);
  digitalWrite(MOTOR_A_IN2, LOW);
  digitalWrite(MOTOR_B_IN1, LOW);
  digitalWrite(MOTOR_B_IN2, LOW);
  digitalWrite(MOTOR_C_IN1, LOW);
  digitalWrite(MOTOR_C_IN2, LOW);
}

void writePin(int pin, bool state) {
  if (state) {
    if (pin == D0) {
      digitalWrite(pin, HIGH);
    } else {
      analogWrite(pin, MOTOR_SPEED);
    }
  } else {
    if (pin != D0) {
      analogWrite(pin, 0);
    }
    digitalWrite(pin, LOW);
  }
}

// -----------------------------------------------------------------------------
// DIRECTION FUNCTIONS
// -----------------------------------------------------------------------------

void executeNORTH() {
  Serial.println("[TEST] >>> EXECUTING NORTH <<<");
  writePin(MOTOR_A_IN1, true);  writePin(MOTOR_A_IN2, false);
  writePin(MOTOR_B_IN1, false); writePin(MOTOR_B_IN2, true);
  writePin(MOTOR_C_IN1, false); writePin(MOTOR_C_IN2, false);
}

void executeSOUTH() {
  Serial.println("[TEST] >>> EXECUTING SOUTH <<<");
  writePin(MOTOR_A_IN1, false); writePin(MOTOR_A_IN2, true);
  writePin(MOTOR_B_IN1, true);  writePin(MOTOR_B_IN2, false);
  writePin(MOTOR_C_IN1, false); writePin(MOTOR_C_IN2, false);
}

void executeNORTHWEST() {
  Serial.println("[TEST] >>> EXECUTING NORTHWEST <<<");
  writePin(MOTOR_A_IN1, true);  writePin(MOTOR_A_IN2, false);
  writePin(MOTOR_B_IN1, false); writePin(MOTOR_B_IN2, false);
  writePin(MOTOR_C_IN1, false); writePin(MOTOR_C_IN2, true);
}

void executeSOUTHEAST() {
  Serial.println("[TEST] >>> EXECUTING SOUTHEAST <<<");
  writePin(MOTOR_A_IN1, false); writePin(MOTOR_A_IN2, true);
  writePin(MOTOR_B_IN1, false); writePin(MOTOR_B_IN2, false);
  writePin(MOTOR_C_IN1, true);  writePin(MOTOR_C_IN2, false);
}

void executeCW() {
  Serial.println("[TEST] >>> EXECUTING CW (Rotate Clockwise) <<<");
  writePin(MOTOR_A_IN1, true);  writePin(MOTOR_A_IN2, false);
  writePin(MOTOR_B_IN1, true);  writePin(MOTOR_B_IN2, false);
  writePin(MOTOR_C_IN1, true);  writePin(MOTOR_C_IN2, false);
}

void executeCCW() {
  Serial.println("[TEST] >>> EXECUTING CCW (Rotate Counter-Clockwise) <<<");
  writePin(MOTOR_A_IN1, false); writePin(MOTOR_A_IN2, true);
  writePin(MOTOR_B_IN1, false); writePin(MOTOR_B_IN2, true);
  writePin(MOTOR_C_IN1, false); writePin(MOTOR_C_IN2, true);
}

// -----------------------------------------------------------------------------
// SETUP & MAIN LOOP
// -----------------------------------------------------------------------------
void setup() {
  Serial.begin(115200);
  delay(500);

  pinMode(MOTOR_A_IN1, OUTPUT); pinMode(MOTOR_A_IN2, OUTPUT);
  pinMode(MOTOR_B_IN1, OUTPUT); pinMode(MOTOR_B_IN2, OUTPUT);
  pinMode(MOTOR_C_IN1, OUTPUT); pinMode(MOTOR_C_IN2, OUTPUT);

  stopMotors();

  Serial.println("\n==================================================");
  Serial.println("  ESP-12E STANDALONE DIRECTION TEST (NO WI-FI)   ");
  Serial.println("==================================================");
}

void loop() {
  // 1. NORTH (3 Seconds)
  executeNORTH();
  delay(3000);
  stopMotors();
  delay(2000);

  // 2. SOUTH (3 Seconds)
  executeSOUTH();
  delay(3000);
  stopMotors();
  delay(2000);

  // 3. NORTHWEST (3 Seconds)
  executeNORTHWEST();
  delay(3000);
  stopMotors();
  delay(2000);

  // 4. SOUTHEAST (3 Seconds)
  executeSOUTHEAST();
  delay(3000);
  stopMotors();
  delay(2000);

  // 5. CW - Rotate Clockwise (3 Seconds)
  executeCW();
  delay(3000);
  stopMotors();
  delay(2000);

  // 6. CCW - Rotate Counter-Clockwise (3 Seconds)
  executeCCW();
  delay(3000);
  stopMotors();
  delay(2000);
}
