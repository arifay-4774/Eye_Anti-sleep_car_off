#include <SoftwareSerial.h>

SoftwareSerial BT(10, 11); // RX, TX

// Motor A (Left)
int IN1 = 2;
int IN2 = 3;

// Motor B (Right)
int IN3 = 4;
int IN4 = 5;

void setup() {
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);

  BT.begin(9600);
  Serial.begin(9600);

  stopCar(); // Start stopped
}

void loop() {
  if (BT.available()) {
    char cmd = BT.read();
    Serial.println(cmd);

    if (cmd == 'F') {
      moveForward();
    } else if (cmd == 'S') {
      stopCar();
    }
  }
}

void moveForward() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void stopCar() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}