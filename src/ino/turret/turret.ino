#include <Wire.h>

// Constants
#define I2C_ADDR 0xe6

// Gun
#define GUN_SPR 200  // steps per revolution
#define GUN_MIN_DELAY 3000  // lowest delay between pulses, in us
#define GUN_EN 6
#define GUN_DR 5
#define GUN_ST 4

// Gimbal
#define GIM_SPR 2048
#define GIM_MIN_DELAY 2000
#define GIM_UPPER 40  // upper limit
#define GIM_LOWER -15 // lower limit
#define GIM_EN 9
#define GIM_DR 8
#define GIM_ST 7

unsigned long ct;

int gunStep;
int gunDelay;
int gunTimes;
bool gunReturning;
bool gunEnabled;

int gimStep;
int gimTarget;
int gimDelay;
bool gimEnabled;

void setup() {

  Serial.begin(115200);
  
  Serial.println("Initializing pins");
  pinMode(GUN_EN, OUTPUT);
  pinMode(GUN_DR, OUTPUT);
  pinMode(GUN_ST, OUTPUT);
  pinMode(GIM_EN, OUTPUT);
  pinMode(GIM_DR, OUTPUT);
  pinMode(GIM_ST, OUTPUT);

  setEnabled('t', true);
  setEnabled('g', true);

  Serial.println("Initializing I2C");
  Wire.begin(I2C_ADDR);
  Wire.onReceive(onRcv);
}

void loop() {
  ct = micros();
  
}

void onRcv(int bytes) {
  
  char first = Wire.read();
  
  switch (first) {
    
    case 'm': {  // Move gimbal (4bf: angle, 4bf: speed)
      float angle = constrain(readFloat(), GIM_LOWER, GIM_UPPER);
      float speed = readFloat();
      if (angle > GIM_UPPER || angle < GIM_LOWER) {
        break;
      }
      gimTarget = GIM_SPR*angle/360;
      gimDelay = max(360/(float(GIM_SPR)*angle), GIM_MIN_DELAY);
    }
    break;
    case 's':  // Stop gimbal
      gimTarget = gimStep;
    break;
    case 'a':  // Get current gimbal angle
    break;
    
    case 't': {  // Fire gun (1bi: times, 4bf: RPM)
      gunTimes += Wire.read();
      float rate = readFloat();
      gunDelay = max(60000000/rate, GUN_MIN_DELAY);
    }
    break;
    case 'r':  // Return gun to neutral
      gunReturning = true;
    break;
    case 'q':  // Stop gun
      gunTimes = 0;
      gunReturning = false;
    break;
    
    case 'c':  // Engage motor and calibrate if was disengaged (1bc: motor)
      setEnabled(Wire.read(), true)
    break;
    case 'd':  // Disengage motor (1bc: motor)
      setEnabled(Wire.read(), false)
    break;
    
  }
  clearBuff();
}

void clearBuff() {
  while (Wire.available() > 0) {
    Wire.read();
  }
}

float readFloat() {
  byte buf[4];
  Wire.readBytes(buf, 4);
  return ((float*)buf)[0];
}

void setEnabled(char mot, bool state) {
  switch (mot) {
    case 'g':  // Gimbal
      if (state && !gimEnabled) {  // Rising edge?
        gimSteps = 0;  // Reset the steps
      }
      gimEnabled = state;
      digitalWrite(GIM_EN, !state);  // EN is active low
      break;
    case 't':  // Gun
      if (state && !gunEnabled) {
        gunSteps = 0;
      }
      gunEnabled = state;
      digitalWrite(GUN_EN, !state);
  }
}

