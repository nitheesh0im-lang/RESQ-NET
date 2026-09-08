/*
 * RESQ-NET: Isolated SOUTH Movement Hardware Test
 * 
 * Hardware Pins:
 *  Motor A (Left):  D5, D6
 *  Motor B (Right): D3, D4
 *  Motor C (Rear):  D0, D1
 *  Speed:           150 (PWM)
 * 
 * Logic:
 *  Drives motors in SOUTH direction for 3 seconds, then stops for 2 seconds (looping).
 *  NO WI-FI REQUIRED for this isolated hardware test.
 */

#include <Arduino.h>

const int MOTOR_SPEED = 150;

// Motor A (D5, D6)
const int MOTOR_A_IN1 = D5;
const int MOTOR_A_IN2 = D6;

// Motor B (D3, D4)
const int MOTOR_B_IN1 = D3;
const int MOTOR_B_IN2 = D4;

// Motor C (D0, D1)
const int MOTOR_C_IN1 = D0;
const int MOTOR_C_IN2 = D1;

void stopMotors() {
  digitalWrite(MOTOR_A_IN1, LOW); digitalWrite(MOTOR_A_IN2, LOW);
  digitalWrite(MOTOR_B_IN1, LOW); digitalWrite(MOTOR_B_IN2, LOW);
  digitalWrite(MOTOR_C_IN1, LOW); digitalWrite(MOTOR_C_IN2, LOW);
}

void writePin(int pin, bool state) {
  if (state) {
    if (pin == D0) {
      digitalWrite(pin, HIGH);
    } else {
      analogWrite(pin, MOTOR_SPEED);
    }
  } else {
    digitalWrite(pin, LOW);
  }
}

// Exact SOUTH Movement Condition
void executeSOUTH() {
  Serial.println("[TEST] >>> EXECUTING SOUTH CONDITION <<<");
  Serial.println("  Motor A (D5, D6): BACKWARD (D5=LOW, D6=150)");
  Serial.println("  Motor B (D3, D4): FORWARD  (D3=150, D4=LOW)");
  Serial.println("  Motor C (D0, D1): STOP     (D0=LOW, D1=LOW)");

  // Motor A: Backward
  writePin(MOTOR_A_IN1, false);
  writePin(MOTOR_A_IN2, true);

  // Motor B: Forward
  writePin(MOTOR_B_IN1, true);
  writePin(MOTOR_B_IN2, false);

  // Motor C: Stop
  writePin(MOTOR_C_IN1, false);
  writePin(MOTOR_C_IN2, false);
}

void setup() {
  Serial.begin(115200);
  delay(200);

  pinMode(MOTOR_A_IN1, OUTPUT); pinMode(MOTOR_A_IN2, OUTPUT);
  pinMode(MOTOR_B_IN1, OUTPUT); pinMode(MOTOR_B_IN2, OUTPUT);
  pinMode(MOTOR_C_IN1, OUTPUT); pinMode(MOTOR_C_IN2, OUTPUT);

  stopMotors();

  Serial.println("\n==========================================");
  Serial.println("   ISOLATED SOUTH MOVEMENT MOTOR TEST     ");
  Serial.println("==========================================");
}

void loop() {
  // Step 1: Run SOUTH for 3 seconds
  executeSOUTH();
  delay(3000);

  // Step 2: Pause for 2 seconds
  Serial.println("[TEST] Pause / Stop (2 Seconds)...");
  stopMotors();
  delay(2000);
}
